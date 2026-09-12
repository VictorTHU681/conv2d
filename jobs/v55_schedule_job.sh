#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
variants=(baseline weaveall weave3 weave4)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/test_carry.c "build/v55/$v.c" -o "build/v55/tall3_$v" -lm
    gcc "${flags[@]}" tools/test_conv.c "build/v55/$v.c" -o "build/v55/tc3_$v" -lm
    gcc "${flags[@]}" tools/fbench.c "build/v55/$v.c" -o "build/v55/cfb3_$v" -lm
    echo "SIGNED_TALL $v"
    OMP_NUM_THREADS=2 TEST_BITWISE=1 TEST_SIGNED=1 CONV_ROLL=1 "${run[@]}" "build/v55/tall3_$v"
    echo "GENERALIZE $v"
    TEST_BITWISE=1 TEST_SIGNED=1 CONV_ROLL=1 "${run[@]}" "build/v55/tc3_$v" 80 56501
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
            if (( round % 2 == 0 )); then order=(weave4 weave3 weaveall baseline); fi
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "build/v55/cfb3_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "SCHEDULE_DONE $(date -Is)"
