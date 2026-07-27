#!/usr/bin/env python3
"""Make a bazel_to_orfs.sh bundle portable to another machine.

For hermetic designs the RTL / includes / LEF-LIB live in the Bazel cache
($output_base/external/... and bazel-out/...), not the repo — so the extracted
config.mk points at absolute paths that only exist on the build machine.  This
copies every file/dir referenced by the path-bearing config vars into
<inputs>/, and rewrites those tokens to $(PREPARED_INPUTS)/... so the bundle is
self-contained.  bazel_to_orfs.sh's generated run.sh exports PREPARED_INPUTS to the
bundle's own inputs/ dir (derived from run.sh's location), so make expands the
paths correctly wherever the bundle is copied.

Include dirs are copied whole (preserving internal structure, so `include
"pkg/foo.svh"` still resolves against the -I dir).  Files are grouped by a hash
of their source directory to stay unique without long mirrored paths.

Usage: stage_prepared_inputs.py <config.mk> <inputs_dir>
"""
import hashlib
import os
import re
import shutil
import sys

# Vars whose value is one or more file/dir paths (mirrors bazel_to_config_mk.sh).
_PATH_VARS = re.compile(
    r"^(VERILOG_FILES|VERILOG_INCLUDE_DIRS|SDC_FILE|ADDITIONAL_LEFS|"
    r"ADDITIONAL_LIBS|ADDITIONAL_GDS|IO_CONSTRAINTS|FOOTPRINT_TCL|"
    r"MACRO_PLACEMENT_TCL|PDN_TCL)$"
)


def _is_pathvar(key):
    return bool(_PATH_VARS.match(key)) or key.endswith("_TCL")


def _dst_for(src, inputs):
    """Mirror <src> under <inputs> grouped by a hash of its parent dir."""
    src = os.path.realpath(src)
    parent = os.path.dirname(src)
    tag = hashlib.md5(parent.encode()).hexdigest()[:10]
    rel = os.path.join(tag, os.path.basename(src))
    return rel, os.path.join(inputs, rel)


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: stage_prepared_inputs.py <config.mk> <inputs_dir>")
    cfg, inputs = sys.argv[1], sys.argv[2]
    os.makedirs(inputs, exist_ok=True)

    out_lines = []
    copied = 0
    for line in open(cfg):
        m = re.match(r"^(export\s+)?(\w+)\s*(\??=)\s*(.*)$", line.rstrip("\n"))
        if not m:
            out_lines.append(line.rstrip("\n"))
            continue
        prefix, key, assign, val = m.groups()
        if not _is_pathvar(key):
            out_lines.append(line.rstrip("\n"))
            continue
        new_toks = []
        for tok in val.split():
            # Only absolutize real absolute filesystem paths; leave flags,
            # make-vars, and already-relative tokens untouched.
            if not tok.startswith("/") or tok.startswith("-") or "$(" in tok:
                new_toks.append(tok)
                continue
            if not os.path.exists(tok):
                new_toks.append(tok)  # leave dangling tokens as-is
                continue
            rel, dst = _dst_for(tok, inputs)
            if not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.isdir(tok):
                    shutil.copytree(tok, dst, symlinks=False,
                                    ignore_dangling_symlinks=True)
                else:
                    shutil.copy2(os.path.realpath(tok), dst)
                copied += 1
            new_toks.append("$(PREPARED_INPUTS)/" + rel)
        out_lines.append(
            "%s%s%s%s" % (prefix or "", key, assign, " ".join(new_toks))
        )

    with open(cfg, "w") as fh:
        fh.write("\n".join(out_lines) + "\n")
    print("Staged %d input files/dirs into %s" % (copied, inputs), file=sys.stderr)


if __name__ == "__main__":
    main()
