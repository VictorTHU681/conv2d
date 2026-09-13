#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/output-order
sha256sum "$root/baseline.c" "$root/ordered.c"
gcc -O3 -fopenmp tools/test_v54_state.c "$root/ordered.c" -o "$root/state" -lm
for mode in default 0 1 2 3; do
    knobs=(); [[ "$mode" == default ]] || knobs=(CONV_PACKSER="$mode")
    echo "ORDER_STATE pack=$mode"
    env "${knobs[@]}" OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state"
done
gcc -O3 -fopenmp tools/test_v56_planar_full_guard.c "$root/ordered.c" -o "$root/guard" -lm
OMP_NUM_THREADS=7 "${run[@]}" "$root/guard"
for v in baseline ordered; do
    gcc -O3 bench_conv.c "$root/$v.c" -o "$root/official_$v" -lm -fopenmp
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 0 1 2 3; do
            order=(baseline ordered)
            (( round%2==0 )) || order=(ordered baseline)
            for v in "${order[@]}"; do
                echo "OFFICIAL memory=$memory round=$round variant=$v shape=$args"
                report=$("${run[@]}" "$root/official_$v" "${shape[@]}" 5)
                printf '%s\n' "$report"
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "OUTPUT_ORDER_DONE $(date -Is)"
