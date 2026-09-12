#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset CONV_ROLL_STEP
root=build/v56/experiments/k5-default
for v in short2 short4; do
    echo "DEFAULT_VARIANT $v"
    sha256sum "$root/$v.c"
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/state_$v" -lm
    for mode in default 0 1 2 3; do
        knobs=(); [[ "$mode" == default ]] || knobs=(CONV_PACKSER="$mode")
        echo "DEFAULT_STATE variant=$v pack=$mode"
        env "${knobs[@]}" OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state_$v"
    done
    gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/${v}_overlap.c" -o "$root/overlap_$v" -lm
    OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/overlap_$v"
done
echo "K5_DEFAULT_CHECK_DONE $(date -Is)"
