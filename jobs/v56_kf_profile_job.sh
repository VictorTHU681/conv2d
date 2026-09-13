#!/usr/bin/env bash
set -eo pipefail
unset FBENCH_FORCE
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/kf-share
for v in baseline merged; do
    sha256sum "$root/${v}_profile.c"
    gcc -O3 -fopenmp tools/fbench.c "$root/${v}_profile.c" -o "$root/profile_$v" -lm
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 1 2 3 4 5 6; do
            order=(baseline merged); (( round%2==1 )) || order=(merged baseline)
            for v in "${order[@]}"; do
                echo "PROFILE memory=$memory round=$round variant=$v shape=$args"
                CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "KF_PROFILE_DONE $(date -Is)"
