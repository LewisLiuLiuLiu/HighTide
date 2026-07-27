#!/usr/bin/env bash
# Regenerate designs/src/NVDLA/vmod/ from the NVDLA nv_small spec.
#
# NVDLA is the one HighTide design whose RTL is NOT hermetically fetchable: the
# committed vmod/ tree is the *output* of NVDLA's legacy spec build (Perl 5.10 +
# Python 2.7 + JDK11 + SystemC 2.3.0 running `tmake -build vmod` over the
# parameterized nvdla/hw source), which cannot be reproduced as a Bazel genrule.
# So vmod/ stays committed (see BUILD.bazel) and the Bazel build never runs this
# script.  It exists only to refresh vmod/ manually, and clones the pinned
# upstream on demand (the retired dev/repo submodule) — dev/repo/ is gitignored.
set -euo pipefail

DIR="$(dirname $(readlink -f $0))"
cd "$DIR"
export USER=${USER:-no_user}
if [ "$HOME" = "/" ]; then
  HOME=/tmp/
fi

# Fetch the pinned NVDLA hw source (nv_small) into dev/repo/ on demand —
# replaces the retired git submodule so a plain checkout / k8s pod never has to.
NVDLA_HW_SHA=771f20cc9e69759d7277978eb41e8d47f1547374
if [ ! -x repo/tools/bin/tmake ]; then
  rm -rf repo
  git clone --branch nv_small https://github.com/nvdla/hw.git repo
  ( cd repo && git checkout "$NVDLA_HW_SHA" && git submodule update --init --recursive )
fi

# Prerequisite Setup
bash "$(pwd)/install/install_jdk11.sh"
bash "$(pwd)/install/install_openssl.sh"
bash "$(pwd)/install/install_perl5_10.sh"
bash "$(pwd)/install/install_py2_6.sh"
bash "$(pwd)/install/install_systemc2_3_0.sh"

cp tree.make ./repo/tree.make

PKG_ROOT="${DIR}/packages"
PERL_PREFIX="${PKG_ROOT}/perl-5.10.1"
PY_PREFIX="${PKG_ROOT}/python-2.7.18"
PERL="${PERL_PREFIX}/bin/perl"
PYTHON="${PY_PREFIX}/bin/python"
export LD_LIBRARY_PATH="${PY_PREFIX}/lib:${LD_LIBRARY_PATH:-}"

cd repo
${PERL} ./tools/bin/tmake -build vmod
rm outdir/nv_small/vmod/nvdla/cfgrom/*
cp ../NV_NVDLA_cfgrom_REPLACE.v outdir/nv_small/vmod/nvdla/cfgrom/NV_NVDLA_cfgrom.v
cp -r outdir/nv_small/vmod ../../
