#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"
variants=(baseline gather gatherser carrygather)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/fbench.c "build/v54/$v.c" -o "build/v54/gfb_$v" -lm
    if [[ "$v" == baseline ]]; then continue; fi
    gcc "${flags[@]}" tools/test_conv.c "build/v54/$v.c" -o "build/v54/gtc_$v" -lm
    echo "SIGNED_BITWISE $v"
    TEST_SIGNED=1 TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" "build/v54/gtc_$v" 100 54701
done
gcc "${flags[@]}" tools/test_carry.c build/v54/carrygather.c -o build/v54/tall_gather -lm
echo SIGNED_TALL_CARRY_GATHER
OMP_NUM_THREADS=2 TEST_SIGNED=1 TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" build/v54/tall_gather
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 1 2 3; do
            order=("${variants[@]}")
            if (( round % 2 == 0 )); then order=(carrygather gatherser gather baseline); fi
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "build/v54/gfb_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "GATHER_DONE $(date -Is)"
