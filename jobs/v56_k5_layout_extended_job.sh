#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/k5-layout
for v in triplet triplet_out; do
    echo "EXTENDED_VARIANT $v"
    sha256sum "$root/$v.c" "$root/${v}_audit.c" "$root/${v}_overlap.c"
    gcc -O3 -fopenmp -DK5_INPUT_AUDIT tools/test_v56_k5_triplet.c "$root/${v}_audit.c" -o "$root/extended_$v" -lm
    OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/extended_$v"
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/modes_$v" -lm
    for mode in 0 1 2 3; do
        echo "EXTENDED_STATE variant=$v pack=$mode"
        OMP_NUM_THREADS=7 CONV_PACKSER="$mode" CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/modes_$v"
    done
    gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/${v}_overlap.c" -o "$root/overlap_$v" -lm
    OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/overlap_$v"
done
echo "K5_LAYOUT_EXTENDED_DONE $(date -Is)"
