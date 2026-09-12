#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"
variants=(baseline pingpong lookahead own256 own512 static512 owngather)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/fbench.c "build/v54/$v.c" -o "build/v54/sfb_$v" -lm
    if [[ "$v" == baseline ]]; then continue; fi
    gcc "${flags[@]}" tools/test_conv.c "build/v54/$v.c" -o "build/v54/stc_$v" -lm
    echo "SIGNED_BITWISE $v"
    TEST_SIGNED=1 TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" "build/v54/stc_$v" 80 54801
done
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
            if (( round % 2 == 0 )); then order=(owngather static512 own512 own256 lookahead pingpong baseline); fi
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "build/v54/sfb_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "SECOND_DONE $(date -Is)"
