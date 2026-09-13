#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/k5-triplet
sha256sum "$root/baseline.c" "$root/triplet.c"
gcc -O3 -fopenmp tools/test_v54_state.c "$root/triplet.c" -o "$root/state" -lm
OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state"
for v in baseline triplet; do
    gcc -O3 -fopenmp tools/fbench.c "$root/$v.c" -o "$root/bench_$v" -lm
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
            order=(baseline triplet); (( round%2==1 )) || order=(triplet baseline)
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "$root/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "K5_SMOKE_DONE $(date -Is)"
