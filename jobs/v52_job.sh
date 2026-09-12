#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v52_setup.sh"
variants=(baseline cache nf4 mix early align6 align7 nf4mix)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/test_conv.c "build/v52/$v.c" -o "build/v52/test_$v" -lm
    gcc "${flags[@]}" tools/fbench.c "build/v52/$v.c" -o "build/v52/fbench_$v" -lm
    echo "GENERALIZE $v"
    TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" "build/v52/test_$v" 40 52201
    echo "SIGNED $v"
    TEST_SIGNED=1 TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" "build/v52/test_$v" 40 52202
done
for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    for round in 1 2 3; do
        order=("${variants[@]}")
        if (( round % 2 == 0 )); then
            order=()
            for (( i=${#variants[@]}-1; i>=0; i-- )); do order+=("${variants[i]}"); done
        fi
        for v in "${order[@]}"; do
            echo "MEASURE round=$round variant=$v shape=$args"
            "${run[@]}" "build/v52/fbench_$v" "${shape[@]}" 5
        done
    done
    for pd in 1 2 3 4 6 8 12; do
        echo "MEASURE round=1 variant=pd$pd shape=$args"
        CONV_ROLL_PD=$pd "${run[@]}" build/v52/fbench_cache "${shape[@]}" 5
    done
done
echo "DONE $(date -Is)"
