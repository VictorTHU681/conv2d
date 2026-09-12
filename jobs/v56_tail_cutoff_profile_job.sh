#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP
root=build/v56/experiments/tail-cutoff
sha256sum "$root/fbench.c"
for v in baseline guided cut2 cut4; do
    sha256sum "$root/${v}_profile.c"
    gcc -O3 -fopenmp "$root/fbench.c" "$root/${v}_profile.c" -o "$root/profile_$v" -lm
done
orders=('baseline guided cut4 cut2' 'guided cut2 baseline cut4'
        'cut2 cut4 guided baseline' 'cut4 baseline cut2 guided')
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
echo "TAIL_CUTOFF_PROFILE_DONE $(date -Is)"
