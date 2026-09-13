#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP
root=build/v56/experiments/guided-chunks
sha256sum "$root/fbench.c" "$root/grow2_profile.c"
gcc -O3 -fopenmp "$root/fbench.c" "$root/grow2_profile.c" -o "$root/profile_same" -lm
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for round in 0 1 2 3 4 5; do
        if (( round%2==0 )); then order=(fixed guided); else order=(guided fixed); fi
        for v in "${order[@]}"; do
            echo "PROFILE memory=$memory round=$round variant=$v shape=6144 4096 41 41"
            if [[ "$v" == fixed ]]; then
                CONV_ROLL_STEP=2 CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile_same" 6144 4096 41 41 5
            else
                CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile_same" 6144 4096 41 41 5
            fi
        done
    done
done
echo "GUIDED_SAME_BINARY_DONE $(date -Is)"
