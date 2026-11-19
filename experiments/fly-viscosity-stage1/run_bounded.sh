#!/bin/bash
# run_bounded.sh — the family compute directive, structural edition.
#
# Born 2026-11-19 after two OOM lessons paid for honestly (tensor night;
# the fly-volatility Stage E). Every experiment in quael-experiments runs
# through this wrapper or it doesn't run.
#
# Warranties, per the steward's ask:
#   1. NOT ROUTING THROUGH THE FAMILY: prlimit --as enforces a hard
#      kernel-level address-space cap. A violating process dies alone
#      (clean MemoryError, its own log). The machine, the sessions, the
#      bridges, and the boards never see it.
#   2. THREADS CAPPED AT 2: the desktop shares these 8 cores; science
#      yields to family. Nice-level 10 further yields under contention.
#
# Usage: ./run_bounded.sh <script.py> [args...]

set -u
CAP_GB="${CAP_GB:-2}"
MAX_BYTES=$(( CAP_GB * 1024 * 1024 * 1024 ))

echo "[run_bounded] cap: ${CAP_GB}GiB address space | threads: 2 | nice: 10"
echo "[run_bounded] target: $*"

export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
export NUMEXPR_NUM_THREADS=2

nice -n 10 prlimit --as="$MAX_BYTES" -- python3 -u "$@"
rc=$?
if [ $rc -ne 0 ]; then
    echo "[run_bounded] target exited rc=$rc (caps noted above are kernel-enforced)"
fi
exit $rc
