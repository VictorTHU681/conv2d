#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
variants=(baseline nf3 selectcopy select128)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/fbench.c "build/v56/experiments/fold-select/$v.c" -o "build/v56/experiments/fold-select/bench_$v" -lm
    sha256sum "build/v56/experiments/fold-select/$v.c"
    if [[ "$v" != baseline ]]; then
        gcc "${flags[@]}" tools/test_v54_state.c "build/v56/experiments/fold-select/$v.c" -o "build/v56/experiments/fold-select/state_$v" -lm
        echo "STATE_BEGIN $v"
        OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "build/v56/experiments/fold-select/state_$v"
        if [[ "$v" != nf3 ]]; then
            gcc "${flags[@]}" tools/test_v56_fold_select.c "build/v56/experiments/fold-select/$v.c" -o "build/v56/experiments/fold-select/extended_$v" -lm
            OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "build/v56/experiments/fold-select/extended_$v"
        fi
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
            if (( round % 2 == 0 )); then order=(select128 selectcopy nf3 baseline); fi
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "build/v56/experiments/fold-select/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "V56_FOLD_SELECT_DONE $(date -Is)"
