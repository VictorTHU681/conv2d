#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
variants=(baseline nf3 f3copy f3copy128)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/fbench.c "build/v56/experiments/fold-copy/$v.c" -o "build/v56/experiments/fold-copy/bench_$v" -lm
    sha256sum "build/v56/experiments/fold-copy/$v.c"
    if [[ "$v" != baseline ]]; then
        gcc "${flags[@]}" tools/test_v54_state.c "build/v56/experiments/fold-copy/$v.c" -o "build/v56/experiments/fold-copy/state_$v" -lm
        echo "STATE_BEGIN $v"
        OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "build/v56/experiments/fold-copy/state_$v"
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
            if (( round % 2 == 0 )); then order=(f3copy128 f3copy nf3 baseline); fi
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "build/v56/experiments/fold-copy/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "V56_FOLD_COPY_DONE $(date -Is)"
