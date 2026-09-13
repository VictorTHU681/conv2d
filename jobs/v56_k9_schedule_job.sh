#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
variants=(baseline k9weave k9split k9both)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/test_v55_nine.c "build/v56/$v.c" -o "build/v56/nine_$v" -lm
    gcc "${flags[@]}" tools/test_conv.c "build/v56/$v.c" -o "build/v56/general_$v" -lm
    gcc "${flags[@]}" tools/fbench.c "build/v56/$v.c" -o "build/v56/bench_$v" -lm
    echo "EXTENDED_K9 $v"
    OMP_NUM_THREADS=2 TEST_BITWISE=1 TEST_SIGNED=1 CONV_ROLL=1 "${run[@]}" "build/v56/nine_$v"
    echo "GENERALIZE $v"
    TEST_BITWISE=1 TEST_SIGNED=1 CONV_ROLL=1 "${run[@]}" "build/v56/general_$v" 80 56901
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 1 2 3 4 5; do
            order=("${variants[@]}")
            if (( round % 2 == 0 )); then order=(k9both k9split k9weave baseline); fi
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "build/v56/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "K9_SCHEDULE_DONE $(date -Is)"
