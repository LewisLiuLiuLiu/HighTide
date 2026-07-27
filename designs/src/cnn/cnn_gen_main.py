"""Hermetic entry point for the NNgen CNN accelerator RTL generator.

Runs the upstream examples/cnn/cnn.py model builder (from @nngen_src) with
simulation disabled.  With simtype=None, cnn.run() emits the accelerator via
ng.to_ipxact() into <cwd>/cnn_v*/hdl/cnn.v and then calls sys.exit(); we catch
that, locate the generated HDL, and copy it to the requested output path.

The generated RTL is value-independent (weights are streamed in over the AXI
master, not embedded), so the random example weights do not affect cnn.v.

Usage: cnn_gen <output.v>
"""
import glob
import os
import shutil
import sys


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: cnn_gen <output.v>")
    output_path = os.path.abspath(sys.argv[1])

    # The example assigns random int8 weights (np.random); NNgen's quantizer
    # bakes a handful of per-layer requantization shift amounts (cparam_*_cshamt)
    # into the RTL, so the *unseeded* upstream flow produced a non-reproducible
    # cnn.v.  Seed both RNGs to make the generated RTL byte-deterministic across
    # builds (these are demo weights — the shift constants feed constant assigns
    # that synthesis folds identically, so PPA is unaffected by the seed choice).
    import random
    import numpy as np
    random.seed(0)
    np.random.seed(0)

    # cnn.run() writes cnn_v*/hdl/cnn.v relative to cwd; run in a scratch cwd.
    from examples.cnn import cnn

    try:
        cnn.run(simtype=None, silent=False, verilog_filename=output_path)
    except SystemExit as exc:
        # NNgen's example calls sys.exit() once the RTL is emitted (sim off);
        # only a nonzero/none-zero code is a real failure.
        if exc.code not in (None, 0):
            raise

    candidates = glob.glob(os.path.join(os.getcwd(), "cnn_v*", "hdl", "cnn.v"))
    if not candidates:
        raise FileNotFoundError("Unable to locate generated cnn_v*/hdl/cnn.v")
    source = max(candidates, key=os.path.getmtime)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    shutil.copy2(source, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
