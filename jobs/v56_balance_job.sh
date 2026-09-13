#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
variants=(baseline w110 w125)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/fbench.c "build/v56/balance/$v.c" -o "build/v56/balance/bench_$v" -lm
    sha256sum "build/v56/balance/$v.c"
    if [[ "$v" != baseline ]]; then
        gcc "${flags[@]}" tools/test_v54_state.c "build/v56/balance/$v.c" -o "build/v56/balance/state_$v" -lm
        echo "STATE_BEGIN $v"
        OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "build/v56/balance/state_$v"
    fi
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for round in 1 2 3 4 5; do
        order=("${variants[@]}")
        if (( round % 2 == 0 )); then order=(w125 w110 baseline); fi
        for v in "${order[@]}"; do
            echo "MEASURE memory=$memory round=$round variant=$v shape=6390 4256 81 81"
            "${run[@]}" "build/v56/balance/bench_$v" 6390 4256 81 81 5
        done
    done
    for v in "${variants[@]}"; do
        echo "PHASE memory=$memory variant=$v shape=6390 4256 81 81"
        CONV_ROLL_DIAG=1 "${run[@]}" "build/v56/balance/bench_$v" 6390 4256 81 81 3
    done
done
echo "V56_BALANCE_DONE $(date -Is)"
