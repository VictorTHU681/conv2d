#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP
root=build/v56/experiments/fold-param
sha256sum "$root/fbench.c"
for v in baseline cf4 cf34; do
    sha256sum "$root/$v.c" "$root/${v}_profile.c"
    gcc -O3 -fopenmp "$root/fbench.c" "$root/${v}_profile.c" -o "$root/profile_$v" -lm
done
orders=('baseline cf4 cf34' 'cf4 cf34 baseline' 'cf34 baseline cf4')
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 0 1 2; do
            read -ra order <<< "${orders[$round]}"
            for v in "${order[@]}"; do
                echo "PARAM_PROFILE memory=$memory round=$round variant=$v shape=$args"
                CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "PARAM_PROFILE_DONE $(date -Is)"
