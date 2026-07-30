# LiteEth

## Quick Start

```bash
bazel build //designs/<platform>/liteeth:liteeth_final
# e.g.
bazel build //designs/nangate45/liteeth:liteeth_final
```

The Verilog top module is `liteeth_udp_usp_gth_sgmii` (LiteX-generated);
the Bazel target / display name is the shorter `liteeth`.

The RTL is generated hermetically by Bazel from the pinned LiteX / migen /
liteeth archives in the root `MODULE.bazel`.  To regenerate against newer
upstream, bump those archive pins and rebuild:

```bash
bazel build //designs/nangate45/liteeth:liteeth_final
```

This initializes the `designs/src/liteeth/dev/repo` submodule and
runs `designs/src/liteeth/dev/setup.sh` to (re)generate the Verilog.

---

## Current configuration

LiteEth is wired up as a single HighTide design: a UDP endpoint over the
Xilinx UltraScale+ GTH-SerDes SGMII PHY (Verilog top
`liteeth_udp_usp_gth_sgmii`).  The other configurations the LiteX
`gen.sh` script can produce — `mac_axi_mii`, `mac_wb_mii`,
`udp_raw_rgmii`, `udp_stream_rgmii`, `udp_stream_sgmii` — are not
currently checked in as HighTide build targets; they were removed in the
2026-05-12 simplification (see `DECISIONS.md`).
