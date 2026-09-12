#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE
root=build/v56/experiments/kf-share
sha256sum "$root/toggle.c"
gcc -O3 -fopenmp tools/test_v54_state.c "$root/toggle.c" -o "$root/toggle_state" -lm
gcc -O3 -fopenmp tools/fbench.c "$root/toggle.c" -o "$root/toggle_bench" -lm
for enabled in 0 1; do
    echo "TOGGLE_STATE enabled=$enabled"
    CONV_KF_SHARE="$enabled" OMP_NUM_THREADS=7 TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/toggle_state"
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 0 1 2 3 4 5; do
            order=(0 1); (( round%2==0 )) || order=(1 0)
            for enabled in "${order[@]}"; do
                echo "TOGGLE memory=$memory round=$round enabled=$enabled shape=$args"
                CONV_KF_SHARE="$enabled" "${run[@]}" "$root/toggle_bench" "${shape[@]}" 5
            done
        done
    done
done
echo "KF_TOGGLE_DONE $(date -Is)"
