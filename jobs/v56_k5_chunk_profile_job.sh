#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE
root=build/v56/experiments/k5-chunks
sha256sum "$root/candidate.c" "$root/candidate_profile.c" "$root/fbench.c" tools/v55_pmu_driver.c
gcc -O3 -fopenmp "$root/fbench.c" "$root/candidate_profile.c" -o "$root/profile" -lm
gcc -O3 -fopenmp tools/v55_pmu_driver.c "$root/candidate.c" -o "$root/steady_pmu" -lm
orders=('8 2 4' '2 4 8' '4 8 2' '4 2 8' '8 4 2' '2 8 4')
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for round in 0 1 2 3 4 5; do
        read -ra order <<< "${orders[$round]}"
        for step in "${order[@]}"; do
            echo "PROFILE memory=$memory round=$round variant=s$step shape=6144 4096 41 41"
            CONV_ROLL_STEP="$step" CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile" 6144 4096 41 41 5
        done
    done
    for round in 0 1 2 3 4 5; do
        read -ra order <<< "${orders[$round]}"
        for step in "${order[@]}"; do
            echo "CHUNK_PMU memory=$memory round=$round step=$step shape=6144 4096 41 41 runs=200"
            CONV_ROLL_STEP="$step" perf stat -x, -e cycles:u,instructions:u,L1-dcache-loads:u,L1-dcache-load-misses:u -- "${run[@]}" "$root/steady_pmu" 6144 4096 41 41 200
        done
    done
done
echo "K5_CHUNK_THREAD_DONE $(date -Is)"
