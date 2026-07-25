"""Rewrite NNgen's inferred `ram_w<W>_l<L>_*` register-array memory modules
into thin wrappers instantiating the matching `fakeram_w<W>_l<L>` macro.

This is the stdlib-only core of the retired dev/replace_rams_with_fakerams.sh
(the venv/backup/macro-copy/packaging orchestration is dropped — under Bazel
the fakeram behavioural stubs are committed local files in the :rtl filegroup,
and the fakeram module name is derived purely from the ram module's base name).
The module-parse and wrapper-emission logic is byte-for-byte identical to the
original, so the produced cnn.v matches the previously-committed one exactly.

Usage: replace_rams <cnn.v>   (rewrites in place)
"""
import re
import sys
from pathlib import Path

MEM_RE = re.compile(r'reg\s+\[(\d+)\s*-\s*1:0\]\s+mem\s*\[\s*0\s*:\s*(\d+)\s*-\s*1\s*\];')
PORT_RE = re.compile(r'(input|output)\s+(?:\[(.+?)\]\s*)?(\w+)$')
BASE_RE = re.compile(r'(ram_w\d+_l\d+)')


def parse_width(expr):
    if not expr:
        return 1
    expr = expr.replace(' ', '')
    if expr.endswith(':0'):
        expr = expr[:-2]
    if '-' in expr:
        val = expr.split('-')[0]
        return int(val)
    if expr.isdigit():
        return int(expr) + 1
    raise ValueError("Unsupported range expression: %s" % expr)


def parse_module(module_lines):
    module_decl = module_lines[0].strip()
    parts = module_decl.split()
    if len(parts) < 2:
        return None
    module_name = parts[1]

    header_lines = []
    header_end_idx = None
    for idx, line in enumerate(module_lines):
        header_lines.append(line)
        if line.strip().endswith(');'):
            header_end_idx = idx
            break
    if header_end_idx is None:
        return None

    port_lines = header_lines[1:]
    groups = {}
    bits = None
    addr_width = None
    clk_signal = None

    for raw_line in port_lines:
        stripped = raw_line.strip().rstrip(',')
        if not stripped or stripped == ');':
            continue
        match = PORT_RE.match(stripped)
        if not match:
            continue
        direction, range_expr, name = match.groups()
        if name == 'CLK':
            clk_signal = name
            continue
        if not name.startswith(module_name + '_'):
            continue
        suffix = name[len(module_name) + 1:]
        if not suffix:
            continue
        parts = suffix.split('_', 1)
        if len(parts) != 2:
            continue
        group_id, field = parts
        field = field.lower()
        bucket = groups.setdefault(group_id, {})
        bucket[field] = name
        if direction == 'output' and field == 'rdata':
            bits = parse_width(range_expr)
        if direction == 'input' and field == 'addr':
            addr_width = parse_width(range_expr)

    mem_match = None
    for body_line in module_lines[header_end_idx + 1:-1]:
        mem_match = MEM_RE.search(body_line)
        if mem_match:
            break
    if not mem_match:
        return None

    mem_bits = int(mem_match.group(1))
    depth = int(mem_match.group(2))
    if bits is None:
        bits = mem_bits
    if addr_width is None:
        addr_width = int((depth - 1).bit_length())
    base_match = BASE_RE.match(module_name)
    base = base_match.group(1) if base_match else module_name

    return {
        'name': module_name,
        'header_idx': header_end_idx,
        'groups': groups,
        'bits': bits,
        'mem_bits': mem_bits,
        'addr_width': addr_width,
        'depth': depth,
        'base': base,
        'clk': clk_signal or 'CLK',
    }


def generate_wrapper(info, fakeram_name):
    header_lines = info['header_lines']
    groups = info['groups']
    clk = info['clk']
    ordered_groups = sorted(groups.items(), key=lambda kv: int(kv[0]))
    conn_entries = []
    for idx, (_, fields) in enumerate(ordered_groups):
        try:
            enable_sig = fields['enable']
            wen_sig = fields.get('wenable') or fields.get('we') or fields.get('writeenable')
            if wen_sig is None:
                raise KeyError('wenable')
            addr_sig = fields['addr']
            wdata_sig = fields['wdata']
            rdata_sig = fields['rdata']
        except KeyError as exc:
            raise RuntimeError("Missing expected signal %s in module %s" % (exc, info['name']))
        conn_entries.extend([
            '    .rw%d_clk(%s)' % (idx, clk),
            '    .rw%d_ce_in(%s)' % (idx, enable_sig),
            '    .rw%d_we_in(%s)' % (idx, wen_sig),
            '    .rw%d_addr_in(%s)' % (idx, addr_sig),
            '    .rw%d_wd_in(%s)' % (idx, wdata_sig),
            '    .rw%d_rd_out(%s)' % (idx, rdata_sig),
        ])
    instance_lines = ['  %s u_%s_mem (' % (fakeram_name, info['name'])]
    for idx, entry in enumerate(conn_entries):
        suffix = ',' if idx + 1 < len(conn_entries) else ''
        instance_lines.append('%s%s' % (entry, suffix))
    instance_lines.append('  );')
    return header_lines + [''] + ['  // Replaced with fakeram macro'] + instance_lines + ['', 'endmodule', '']


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: replace_rams <cnn.v>")
    cnn_path = Path(sys.argv[1])
    lines = cnn_path.read_text().splitlines()

    module_infos = []
    line_idx = 0
    while line_idx < len(lines):
        stripped = lines[line_idx].lstrip()
        if stripped.startswith('module ram_'):
            start = line_idx
            j = line_idx
            header_end = None
            while j < len(lines):
                if lines[j].strip().endswith(');'):
                    header_end = j
                    break
                j += 1
            if header_end is None:
                raise RuntimeError("Malformed module header near line %d" % (line_idx + 1))
            k = header_end + 1
            while k < len(lines) and not lines[k].strip().startswith('endmodule'):
                k += 1
            if k >= len(lines):
                raise RuntimeError("Missing endmodule for module starting at line %d" % (line_idx + 1))
            end = k
            module_lines = lines[start:end + 1]
            parsed = parse_module(module_lines)
            info = {'start': start, 'end': end, 'orig_lines': module_lines}
            if parsed is None:
                info['skip'] = True
            else:
                info.update(parsed)
                info['header_lines'] = module_lines[:parsed['header_idx'] + 1]
            module_infos.append(info)
            line_idx = end + 1
        else:
            line_idx += 1

    if not module_infos:
        print('No ram_ modules found; nothing to replace.')
        return 0

    new_lines = []
    current = 0
    for info in module_infos:
        new_lines.extend(lines[current:info['start']])
        if info.get('skip'):
            new_lines.extend(info['orig_lines'])
        else:
            fakeram_name = info['base'].replace('ram_', 'fakeram_', 1)
            new_lines.extend(generate_wrapper(info, fakeram_name))
        current = info['end'] + 1
    new_lines.extend(lines[current:])

    cnn_path.write_text('\n'.join(new_lines) + '\n')
    replaced = [i['name'] for i in module_infos if not i.get('skip')]
    print("Replaced %d RAM module definitions in %s." % (len(replaced), cnn_path.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
