"""Hermetic entry point for the Snitch clustergen wrapper/pkg generator.

Runs upstream util/clustergen/clustergen.py (from @snitch_cluster_src) twice —
once per template — to emit snitch_cluster_wrapper.sv and snitch_cluster_pkg.sv
from cluster_cfg.json.  Mirrors the retired setup.sh's two clustergen calls.

clustergen.py is an argparse entry point (reads sys.argv); we run it via runpy
with a fresh namespace per template.

Usage: clustergen_gen <cfg> <wrapper_tpl> <out_wrapper> <pkg_tpl> <out_pkg>
"""
import runpy
import sys


def run() -> int:
    if len(sys.argv) < 6:
        sys.exit("usage: clustergen_gen <cfg> <wrapper_tpl> <out_wrapper> <pkg_tpl> <out_pkg>")
    cfg, wrapper_tpl, out_wrapper, pkg_tpl, out_pkg = sys.argv[1:6]
    for tpl, out in ((wrapper_tpl, out_wrapper), (pkg_tpl, out_pkg)):
        sys.argv = ["clustergen", "-c", cfg, "-o", out, "--template", tpl]
        runpy.run_module("clustergen", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
