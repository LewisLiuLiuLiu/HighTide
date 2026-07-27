"""Hermetic entry point for the FlooGen NoC generator.

Runs floogen's `rtl` subcommand (from @floonoc_src) on mesh_config.yml, emitting
the mesh package + top (floo_floonoc_mesh_noc_pkg.sv / floo_floonoc_mesh_noc.sv)
into the output directory.  Mirrors the retired setup.sh invocation
`floogen rtl -c mesh_config.yml -o <outdir> --no-format`.

Usage: floogen_gen <mesh_config.yml> <outdir>
"""
import sys

from floogen.cli import main


def run() -> int:
    if len(sys.argv) < 3:
        sys.exit("usage: floogen_gen <mesh_config.yml> <outdir>")
    config, outdir = sys.argv[1], sys.argv[2]
    # floogen.cli.main() is an argparse entry point — it reads sys.argv itself.
    # --no-format skips the (non-hermetic) verible-verilog-format pass.
    sys.argv = ["floogen", "rtl", "-c", config, "-o", outdir, "--no-format"]
    main()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
