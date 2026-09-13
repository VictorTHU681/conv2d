#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP CONV_ROLL_PD CONV_ROLL_PDIN CONV_ROLL_PDOUT
root=build/v56/experiments/prefetch-split
sha256sum "$root/split.c" "$root/split_profile.c" "$root/fbench.c"
gcc -O3 -fopenmp "$root/fbench.c" "$root/split_profile.c" -o "$root/profile" -lm
sha256sum "$root/profile"
orders=('i3o3 i1o3 i1o1 i3o1' 'i1o3 i3o1 i3o3 i1o1' 'i3o1 i1o1 i1o3 i3o3' 'i1o1 i3o3 i3o1 i1o3')
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 0 1 2 3; do
            read -ra order <<< "${orders[$round]}"
            for cfg in "${order[@]}"; do
                echo "SPLIT_PROFILE memory=$memory round=$round variant=$cfg shape=$args"
                CONV_ROLL_DIAG=1 CONV_ROLL_PDIN="${cfg:1:1}" CONV_ROLL_PDOUT="${cfg:3:1}" "${run[@]}" "$root/profile" "${shape[@]}" 5
            done
        done
    done
done
echo "SPLIT_PROFILE_DONE $(date -Is)"
