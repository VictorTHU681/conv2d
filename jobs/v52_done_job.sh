#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v52_setup.sh"
variants=(baseline done donecopy2)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/test_conv.c "build/v52/$v.c" -o "build/v52/done_test_$v" -lm
    gcc "${flags[@]}" tools/fbench.c "build/v52/$v.c" -o "build/v52/done_fbench_$v" -lm
    echo "SIGNED_BITWISE $v"
    TEST_SIGNED=1 TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" "build/v52/done_test_$v" 80 52501
done
for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    for round in 1 2 3; do
        order=(baseline done donecopy2)
        if (( round % 2 == 0 )); then order=(donecopy2 done baseline); fi
        for v in "${order[@]}"; do
            echo "MEASURE round=$round variant=$v shape=$args"
            "${run[@]}" "build/v52/done_fbench_$v" "${shape[@]}" 7
        done
    done
done
echo "POOL_DONE $(date -Is)"
