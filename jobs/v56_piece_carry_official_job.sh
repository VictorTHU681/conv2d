#!/usr/bin/env bash
set -eo pipefail
unset CONV_ROLL_STEP
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/piece-carry
for v in baseline carry4 combined; do
    gcc -O3 bench_conv.c "$root/$v.c" -o "$root/official_$v" -lm -fopenmp
    sha256sum "$root/$v.c"
done
orders=('baseline carry4 combined' 'carry4 combined baseline' 'combined baseline carry4'
        'combined carry4 baseline' 'baseline combined carry4' 'carry4 baseline combined')
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
echo "PIECE_CARRY_OFFICIAL_DONE $(date -Is)"
