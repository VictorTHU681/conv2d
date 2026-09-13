#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/k33-window
variants=(baseline outline unroll4 ext4 tbl4 tbl8)
# Submit only after the corresponding candidates pass the state/guard sweep.
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/v55_pmu_driver.c "$root/$v.c" -o "$root/pmu_$v" -lm
    sha256sum "$root/$v.c"
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for round in 1 2; do
        order=("${variants[@]}")
        if (( round==2 )); then order=(tbl8 tbl4 ext4 unroll4 outline baseline); fi
        for v in "${order[@]}"; do
            echo "K33_PMU memory=$memory round=$round variant=$v shape=6144 4096 41 41"
            perf stat -x, -e cycles:u,instructions:u,L1-dcache-loads:u,L1-dcache-load-misses:u -- "${run[@]}" "$root/pmu_$v" 6144 4096 41 41 200
        done
    done
done
echo "K33_WINDOW_PMU_DONE $(date -Is)"
