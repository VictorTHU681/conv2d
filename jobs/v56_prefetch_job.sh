#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP CONV_ROLL_PD
root=build/v56/experiments/prefetch-distance
sha256sum "$root/current.c" "$root/fbench.c"
gcc -O3 -fopenmp "$root/fbench.c" "$root/current.c" -o "$root/bench" -lm
sha256sum "$root/bench"
gcc -O3 -fopenmp tools/test_v54_state.c "$root/current.c" -o "$root/state" -lm
gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/current.c" -o "$root/guard" -lm
for pd in 1 2 3 6; do
    echo "PREFETCH_STATE pd=$pd"
    OMP_NUM_THREADS=7 CONV_ROLL_PD="$pd" TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/state"
    echo "PREFETCH_GUARD pd=$pd"
    OMP_NUM_THREADS=7 CONV_ROLL_PD="$pd" "${run[@]}" "$root/guard"
done
# Four-treatment Williams order; every setting occupies each position once.
orders=('3 1 6 2' '1 2 3 6' '2 6 1 3' '6 3 2 1')
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 0 1 2 3; do
            read -ra order <<< "${orders[$round]}"
            for pd in "${order[@]}"; do
                echo "PREFETCH memory=$memory round=$round pd=$pd shape=$args"
                CONV_ROLL_PD="$pd" "${run[@]}" "$root/bench" "${shape[@]}" 5
            done
        done
    done
done
echo "PREFETCH_DONE $(date -Is)"
