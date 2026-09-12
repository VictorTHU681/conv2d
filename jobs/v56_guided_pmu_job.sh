#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP CONV_ROLL_DIAG
root=build/v56/experiments/guided-chunks
sha256sum "$root/grow2.c" "$root/pmu_driver.c"
gcc -O3 -fopenmp "$root/pmu_driver.c" "$root/grow2.c" -o "$root/steady_pmu" -lm
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for round in 0 1 2 3 4 5; do
        if (( round%2==0 )); then order=(fixed guided); else order=(guided fixed); fi
        for v in "${order[@]}"; do
            echo "GUIDED_PMU memory=$memory round=$round variant=$v shape=6144 4096 41 41 runs=200"
            if [[ "$v" == fixed ]]; then
                CONV_ROLL_STEP=2 perf stat -x, -e cycles:u,instructions:u,L1-dcache-loads:u,L1-dcache-load-misses:u -- "${run[@]}" "$root/steady_pmu" 6144 4096 41 41 200
            else
                perf stat -x, -e cycles:u,instructions:u,L1-dcache-loads:u,L1-dcache-load-misses:u -- "${run[@]}" "$root/steady_pmu" 6144 4096 41 41 200
            fi
        done
    done
done
echo "GUIDED_PMU_DONE $(date -Is)"
