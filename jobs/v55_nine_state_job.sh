#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
for v in nine_w130 nine_w140; do
    gcc "${flags[@]}" tools/test_v55_nine.c "build/v55/$v.c" -o "build/v55/state_$v" -lm
    echo "NINE_EXTENDED variant=$v"
    OMP_NUM_THREADS=2 TEST_BITWISE=1 TEST_SIGNED=1 CONV_ROLL=1 "${run[@]}" "build/v55/state_$v"
done
echo "NINE_STATE_DONE $(date -Is)"
