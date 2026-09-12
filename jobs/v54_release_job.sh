#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"
for v in baseline candidate; do
    src=$v; if [[ "$v" == candidate ]]; then src=release; fi
    gcc -O3 bench_conv.c "build/v54/$src.c" -o "build/v54/rel_off_$v" -lm -fopenmp
    sha256sum "build/v54/$src.c"
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
            order=(baseline candidate)
            if (( round % 2 == 0 )); then order=(candidate baseline); fi
            for v in "${order[@]}"; do
                echo "OFFICIAL memory=$memory round=$round variant=$v shape=$args"
                report=$("${run[@]}" "build/v54/rel_off_$v" "${shape[@]}" 5)
                printf '%s\n' "$report"
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "RELEASE_OFFICIAL_DONE $(date -Is)"
