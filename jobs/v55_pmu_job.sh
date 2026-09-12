#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
for v in baseline ntall; do
    gcc "${flags[@]}" tools/v55_pmu_driver.c "build/v55/$v.c" -o "build/v55/pmu_$v" -lm
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 1 2; do
            order=(baseline ntall)
            if (( round == 2 )); then order=(ntall baseline); fi
            for v in "${order[@]}"; do
                echo "PMU memory=$memory round=$round variant=$v shape=$args"
                perf stat -x, -e cycles:u,instructions:u,L1-dcache-loads:u,L1-dcache-load-misses:u -- "${run[@]}" "build/v55/pmu_$v" "${shape[@]}" 200
            done
        done
    done
done
echo "PMU_DONE $(date -Is)"
