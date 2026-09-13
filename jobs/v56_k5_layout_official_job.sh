#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/k5-layout
for v in baseline triplet triplet_out; do
    gcc -O3 bench_conv.c "$root/$v.c" -o "$root/official_$v" -lm -fopenmp
    sha256sum "$root/$v.c"
done
orders=('baseline triplet triplet_out' 'triplet triplet_out baseline' 'triplet_out baseline triplet'
        'triplet_out triplet baseline' 'baseline triplet_out triplet' 'triplet baseline triplet_out')
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 0 1 2 3 4 5; do
            read -ra order <<< "${orders[$round]}"
            for v in "${order[@]}"; do
                echo "OFFICIAL memory=$memory round=$round variant=$v shape=$args"
                report=$("${run[@]}" "$root/official_$v" "${shape[@]}" 5)
                printf '%s\n' "$report"
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "K5_LAYOUT_OFFICIAL_DONE $(date -Is)"
