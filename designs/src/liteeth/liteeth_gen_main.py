"""Hermetic entry point for the LiteEth standalone-core generator.

Runs upstream `liteeth/gen.py` (from @liteeth_src) via runpy so it executes its
`if __name__ == "__main__": main()` path.  gen.py writes the core to
build/gateware/liteeth_core.v relative to the current working directory, so the
calling genrule invokes this from a fresh temp dir and captures that file.

Usage: liteeth_gen <config.yml>
"""
import runpy
import sys

if len(sys.argv) < 2:
    sys.exit("usage: liteeth_gen <config.yml>")

sys.argv = ["liteeth.gen", sys.argv[1]]
runpy.run_module("liteeth.gen", run_name="__main__")
