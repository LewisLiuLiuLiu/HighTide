---
name: find-designs
description: Search for new open-source hardware designs that would be good candidates for the HighTide2 benchmark suite and open GitHub issues to propose them.
argument-hint: "[optional: category or keyword to focus on, e.g. 'processors', 'accelerators', 'peripherals']"
---

# Find New Benchmark Designs

Search for interesting open-source hardware designs that would be good additions to the HighTide2 benchmark suite, then open GitHub issues to propose adding them.

## Selection Criteria

A good candidate design should meet ALL of these:

1. **Open-source license** — Must be publicly available on GitHub (or similar) with a permissive or copyleft license
2. **Synthesizable RTL** — Must have synthesizable Verilog, SystemVerilog, Chisel, LiteX/Migen, Veriloggen, or another HDL that can be converted to plain Verilog
3. **Reasonable complexity** — Should be a meaningful design (not trivial), but not so large that it cannot complete the ORFS flow in reasonable time
4. **Interesting for benchmarking** — Designs that stress different parts of the EDA flow are valuable: high gate count, many macros, complex clock trees, high IO count, deep pipelines, etc.
5. **Diverse** — Prefer designs that add variety to the suite (different application domains, different design styles, different complexity levels)

## Design Categories to Consider

- **Processors**: RISC-V cores (various pipeline depths), GPUs, DSPs
- **Accelerators**: ML/AI accelerators, cryptographic engines, signal processing, compression
- **Peripherals**: Network controllers (Ethernet, USB, PCIe, SPI, I2C, UART), memory controllers, DMA engines
- **SoC components**: Bus interconnects, cache hierarchies, interrupt controllers
- **Domain-specific**: Video/image processing, audio, software-defined radio

## Current Designs (do NOT propose duplicates)

Check the existing designs before proposing:
- gemmini (ML systolic array accelerator)
- minimax (RISC-V core)
- NyuziProcessor (RISC processor)
- lfsr_prbs_gen (LFSR/PRBS generator)
- liteeth (Ethernet MAC, multiple variants)
- cnn (CNN accelerator via NNgen/Veriloggen)
- sha3 (SHA3 hash, in progress)

Also check open GitHub issues for already-proposed designs:
```bash
gh issue list --state open --limit 50
```

## Search Process

1. **Search the web** for open-source hardware designs using queries like:
   - "open source RISC-V core github synthesizable"
   - "open source hardware accelerator RTL github"
   - "open source FPGA IP core verilog"
   - Site-specific: "site:github.com FPGA verilog core"
   - If the user provided a category focus (`$ARGUMENTS`), tailor searches to that area

2. **Evaluate each candidate** against the selection criteria above. For each promising design, check:
   - The GitHub repo: stars, activity, license, documentation quality
   - RTL source availability and language (Verilog/SV/Chisel/etc.)
   - Top-level module ports (clock, reset, data buses) — is it self-contained enough to run through ORFS?
   - Memory usage — does it have large SRAMs that would need FakeRAM?
   - Approximate size/complexity

3. **Check for duplicates** against both the existing designs in the repo AND open GitHub issues.

## Opening Issues

For each viable candidate, open a GitHub issue:

```bash
gh issue create --title "Add <design-name>" --label "enhancement" --body "$(cat <<'ISSUE_EOF'
## Design: <design-name>

**Repository:** <github-url>
**License:** <license>
**Language:** <Verilog/SystemVerilog/Chisel/LiteX/etc.>
**Stars:** <count>

### Description
<1-2 sentence description of what the design does>

### Why it's a good benchmark candidate
<Brief explanation of what makes it interesting for the suite — e.g., stresses routing, has many macros, high IO count, deep pipeline, etc.>

### Estimated complexity
- **Gate count:** <rough estimate if available: small/medium/large>
- **Memories:** <does it use SRAMs/register files that need FakeRAM?>
- **IO count:** <low/medium/high>

### Conversion notes
<What's needed to get plain Verilog — e.g., "pure Verilog, no conversion needed", "SystemVerilog, needs sv2v or yosys-slang", "Chisel, needs JDK + sbt", etc.>

### Target platforms
- [ ] asap7
- [ ] nangate45
- [ ] sky130hd
ISSUE_EOF
)"
```

## Guidelines

- Aim to propose 3-5 quality candidates per invocation, not a huge list of marginal ones
- Prefer designs with recent activity (commits within last 2 years) over abandoned repos
- If a design looks great but has a problematic license, skip it and note why
- If the user specified a focus area (`$ARGUMENTS`), prioritize that category but still ensure diversity
- Do NOT open issues for designs that are already in the repo or already have an open issue
