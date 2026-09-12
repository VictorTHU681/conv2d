#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
for v in baseline previous candidate; do
    gcc -O3 bench_conv.c "build/v56/experiments/first-copy/accept/$v.c" -o "build/v56/experiments/first-copy/accept/off_$v" -lm -fopenmp
    sha256sum "build/v56/experiments/first-copy/accept/$v.c"
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
            order=(baseline previous candidate)
            if (( round % 2 == 0 )); then order=(candidate previous baseline); fi
            for v in "${order[@]}"; do
                echo "OFFICIAL memory=$memory round=$round variant=$v shape=$args"
                report=$("${run[@]}" "build/v56/experiments/first-copy/accept/off_$v" "${shape[@]}" 5)
                printf '%s\n' "$report"
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "OFFICIAL_DONE $(date -Is)"
