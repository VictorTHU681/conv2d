#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP
root=build/v56/experiments/piece-carry
sha256sum "$root/fbench.c"
for v in baseline cached carry4 combined; do
    sha256sum "$root/${v}_profile.c"
    gcc -O3 -fopenmp "$root/fbench.c" "$root/${v}_profile.c" -o "$root/profile_$v" -lm
done
orders=('baseline cached combined carry4' 'cached carry4 baseline combined'
        'carry4 combined cached baseline' 'combined baseline carry4 cached')
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for round in 0 1 2 3; do
        read -ra order <<< "${orders[$round]}"
        for v in "${order[@]}"; do
            echo "PROFILE memory=$memory round=$round variant=$v shape=6144 4096 41 41"
            CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile_$v" 6144 4096 41 41 5
        done
    done
done
echo "PIECE_CARRY_PROFILE_DONE $(date -Is)"
