#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/k5-triplet
for v in baseline triplet; do
    sha256sum "$root/${v}_profile.c"
    gcc -O3 -fopenmp tools/fbench.c "$root/${v}_profile.c" -o "$root/profile_$v" -lm
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41'; do
        read -ra shape <<< "$args"
        for round in 1 2 3; do
            order=(baseline triplet); (( round%2==1 )) || order=(triplet baseline)
            for v in "${order[@]}"; do
                echo "PROFILE memory=$memory round=$round variant=$v shape=$args"
                CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "K5_PROFILE_DONE $(date -Is)"
