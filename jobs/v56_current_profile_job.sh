#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP
root=build/v56/experiments/current-profile
sha256sum "$root/current.c" "$root/current_profile.c" "$root/fbench.c"
gcc -O3 -fopenmp "$root/fbench.c" "$root/current_profile.c" -o "$root/profile" -lm
shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
# Rotate shape order to expose each shape at multiple positions.
for round in 0 1 2 3; do
    for memory in DDR HBM; do
        run=(numactl -N "$cpu_node")
        if [[ "$memory" == HBM ]]; then
            (( hbm_node >= 0 )) || continue
            run+=(--preferred="$hbm_node")
        fi
        for position in 0 1 2 3; do
            index=$(((round+position)%4))
            read -ra shape <<< "${shapes[$index]}"
            echo "CURRENT_PROFILE memory=$memory round=$round shape=${shapes[$index]}"
            CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile" "${shape[@]}" 5
        done
    done
done
echo "CURRENT_PROFILE_DONE $(date -Is)"
