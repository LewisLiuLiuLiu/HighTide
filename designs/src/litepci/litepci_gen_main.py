"""Hermetic entry point for the LitePCIe standalone-core generator.

Runs upstream `litepcie/gen.py` (from @litepci_src) via runpy so it executes its
`if __name__ == "__main__": main()` path.  gen.py writes the core to
build/gateware/litepcie_core.v relative to the current working directory, so the
calling genrule invokes this from a fresh temp dir and captures that file.

Usage: litepci_gen <config.yml>
"""
import runpy
import sys

if len(sys.argv) < 2:
    sys.exit("usage: litepci_gen <config.yml>")

sys.argv = ["litepcie.gen", sys.argv[1]]
runpy.run_module("litepcie.gen", run_name="__main__")
