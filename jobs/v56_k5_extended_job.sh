#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/k5-triplet
sha256sum "$root/triplet.c" "$root/triplet_audit.c"
gcc -O3 -fopenmp -DK5_INPUT_AUDIT tools/test_v56_k5_triplet.c "$root/triplet_audit.c" -o "$root/extended_audit" -lm
OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/extended_audit"
gcc -O3 -fopenmp tools/test_v54_state.c "$root/triplet.c" -o "$root/state_modes" -lm
for mode in 0 1 2 3; do
    echo "K5_STATE pack=$mode"
    OMP_NUM_THREADS=7 CONV_PACKSER="$mode" CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state_modes"
done
echo "K5_EXTENDED_DONE $(date -Is)"
