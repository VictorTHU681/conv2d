#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/output-order
for v in baseline ordered; do
    sha256sum "$root/${v}_audit.c"
    gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/${v}_audit.c" -o "$root/overlap_$v" -lm
    positive=(); [[ "$v" != baseline ]] || positive=(EXPECT_OUTPUT_OVERLAP=1)
    env "${positive[@]}" OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/overlap_$v"
done
echo "OUTPUT_OVERLAP_DONE $(date -Is)"
