#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP CONV_ROLL_PD CONV_ROLL_PDIN CONV_ROLL_PDOUT
root=build/v56/experiments/prefetch-split
sha256sum "$root/split.c" "$root/fbench.c"
gcc -O3 -fopenmp "$root/fbench.c" "$root/split.c" -o "$root/bench" -lm
sha256sum "$root/bench"
gcc -O3 -fopenmp tools/test_v54_state.c "$root/split.c" -o "$root/state" -lm
gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/split.c" -o "$root/guard" -lm
for cfg in i3o3 i1o3 i3o1 i1o1; do
    echo "SPLIT_STATE cfg=$cfg"
    OMP_NUM_THREADS=7 CONV_ROLL_PDIN="${cfg:1:1}" CONV_ROLL_PDOUT="${cfg:3:1}" TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/state"
    echo "SPLIT_GUARD cfg=$cfg"
    OMP_NUM_THREADS=7 CONV_ROLL_PDIN="${cfg:1:1}" CONV_ROLL_PDOUT="${cfg:3:1}" "${run[@]}" "$root/guard"
done
orders=('i3o3 i1o3 i1o1 i3o1' 'i1o3 i3o1 i3o3 i1o1' 'i3o1 i1o1 i1o3 i3o3' 'i1o1 i3o3 i3o1 i1o3')
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
            for cfg in "${order[@]}"; do
                echo "SPLIT memory=$memory round=$round cfg=$cfg shape=$args"
                CONV_ROLL_PDIN="${cfg:1:1}" CONV_ROLL_PDOUT="${cfg:3:1}" "${run[@]}" "$root/bench" "${shape[@]}" 5
            done
        done
    done
done
echo "SPLIT_DONE $(date -Is)"
