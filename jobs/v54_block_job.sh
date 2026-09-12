#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"
variants=(baseline block256 block512 block1024 block2048)
for v in "${variants[@]}" phase; do
    gcc "${flags[@]}" tools/fbench.c "build/v54/$v.c" -o "build/v54/fb_$v" -lm
    gcc "${flags[@]}" tools/test_conv.c "build/v54/$v.c" -o "build/v54/test_$v" -lm
    echo "BITWISE $v"
    TEST_BITWISE=1 TEST_SIGNED=1 CONV_ROLL=1 "${run[@]}" "build/v54/test_$v" 60 54101
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
            if (( round % 2 == 0 )); then order=(block2048 block1024 block512 block256 baseline); fi
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "build/v54/fb_$v" "${shape[@]}" 5
            done
        done
        echo "PHASE memory=$memory shape=$args"
        CONV_ROLL_DIAG=1 "${run[@]}" build/v54/fb_phase "${shape[@]}" 3
    done
done
echo "BLOCK_DONE $(date -Is)"
