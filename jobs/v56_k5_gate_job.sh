#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/k5-layout
sha256sum "$root/gate.c"
for v in triplet triplet_out; do
    echo "GATE_VARIANT $v"
    sha256sum "$root/${v}_audit.c"
    gcc -O3 -fopenmp -I tools -DK5_INPUT_AUDIT "$root/gate.c" "$root/${v}_audit.c" -o "$root/gate_$v" -lm
    OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/gate_$v"
done
echo "K5_GATE_DONE $(date -Is)"
