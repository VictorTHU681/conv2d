#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
variants=(baseline previous align64 align128 prior128)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/fbench.c "build/v56/experiments/k33-align/$v.c" -o "build/v56/experiments/k33-align/bench_$v" -lm
    sha256sum "build/v56/experiments/k33-align/$v.c"
    objdump -d "build/v56/experiments/k33-align/bench_$v" > "results/v56/experiments/k33-align/disas_$v.txt"
    if [[ "$v" == align64 || "$v" == align128 ]]; then
        gcc "${flags[@]}" tools/test_v54_state.c "build/v56/experiments/k33-align/$v.c" -o "build/v56/experiments/k33-align/state_$v" -lm
        echo "STATE_BEGIN $v"
        OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "build/v56/experiments/k33-align/state_$v"
    fi
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
            if (( round % 2 == 0 )); then order=(prior128 align128 align64 previous baseline); fi
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "build/v56/experiments/k33-align/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "V56_K33_ALIGN_DONE $(date -Is)"
