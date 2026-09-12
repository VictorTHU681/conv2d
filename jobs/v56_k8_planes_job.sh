#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
variants=(baseline k8planes)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/test_v55_nine.c "build/v56/$v.c" -o "build/v56/k8_nine_$v" -lm
    gcc "${flags[@]}" tools/test_conv.c "build/v56/$v.c" -o "build/v56/k8_general_$v" -lm
    gcc "${flags[@]}" tools/fbench.c "build/v56/$v.c" -o "build/v56/k8_bench_$v" -lm
    echo "EXTENDED_K9 $v"
    OMP_NUM_THREADS=2 TEST_BITWISE=1 TEST_SIGNED=1 CONV_ROLL=1 "${run[@]}" "build/v56/k8_nine_$v"
    echo "GENERALIZE $v"
    TEST_BITWISE=1 TEST_SIGNED=1 CONV_ROLL=1 "${run[@]}" "build/v56/k8_general_$v" 80 56801
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
            if (( round % 2 == 0 )); then order=(k8planes baseline); fi
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "build/v56/k8_bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "K8_PLANES_DONE $(date -Is)"
