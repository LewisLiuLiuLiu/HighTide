"""Hermetic entry point for the LiteDRAM standalone-core generator.

Runs upstream `litedram/gen.py` (from @litedram_src) via runpy so it executes
its `if __name__ == "__main__": main()` path.  gen.py writes the core to
build/gateware/litedram_core.v relative to the current working directory, so
the calling genrule invokes this from a fresh temp dir and captures that file.

Usage: litedram_gen <config.yml>
"""
import runpy
import sys

if len(sys.argv) < 2:
    sys.exit("usage: litedram_gen <config.yml>")

# gen.py's argparse reads argv[1:]; present ourselves as `litedram.gen`.
sys.argv = ["litedram.gen", sys.argv[1]]
runpy.run_module("litedram.gen", run_name="__main__")
