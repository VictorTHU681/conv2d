#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
for v in baseline coefall; do
    gcc "${flags[@]}" tools/v55_pmu_driver.c "build/v56/experiments/coefficient-cache/coeff/$v.c" -o "build/v56/experiments/coefficient-cache/coeff/pmu_$v" -lm
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
            order=(baseline coefall)
            if (( round == 2 )); then order=(coefall baseline); fi
            for v in "${order[@]}"; do
                echo "PMU memory=$memory round=$round variant=$v shape=$args"
                perf stat -x, -e cycles:u,instructions:u,L1-dcache-loads:u,L1-dcache-load-misses:u -- "${run[@]}" "build/v56/experiments/coefficient-cache/coeff/pmu_$v" "${shape[@]}" 200
            done
        done
    done
done
echo "V56_COEFF_CACHE_PMU_DONE $(date -Is)"
