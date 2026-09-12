#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE
root=build/v56/experiments/k5-cost
for v in baseline triplet k5cost; do
    sha256sum "$root/${v}_profile.c"
    gcc -O3 -fopenmp tools/fbench.c "$root/${v}_profile.c" -o "$root/profile_$v" -lm
done
orders=('baseline triplet k5cost' 'triplet k5cost baseline' 'k5cost baseline triplet'
        'k5cost triplet baseline' 'baseline k5cost triplet' 'triplet baseline k5cost')
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '6144 4096 41 41'; do
        read -ra shape <<< "$args"
        for round in 0 1 2 3 4 5; do
            read -ra order <<< "${orders[$round]}"
            for v in "${order[@]}"; do
                echo "PROFILE memory=$memory round=$round variant=$v shape=$args"
                CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "K5_THREAD_DONE $(date -Is)"
