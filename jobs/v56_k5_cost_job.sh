#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE
root=build/v56/experiments/k5-cost
mkdir -p "$root/disassembly"
for v in baseline triplet k5cost tailcost; do
    sha256sum "$root/$v.c"
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/state_$v" -lm
    echo "COST_STATE variant=$v"
    OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state_$v"
    gcc -O3 -fopenmp tools/fbench.c "$root/$v.c" -o "$root/bench_$v" -lm
    objdump -d "$root/bench_$v" > "$root/disassembly/$v.txt"
done
for v in k5cost tailcost; do
    gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/${v}_overlap.c" -o "$root/overlap_$v" -lm
    echo "COST_OVERLAP variant=$v"
    OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/overlap_$v"
done
# Williams design: each variant occupies each position and follows each other once.
orders=('baseline triplet tailcost k5cost' 'triplet k5cost baseline tailcost'
        'k5cost tailcost triplet baseline' 'tailcost baseline k5cost triplet')
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
            for v in "${order[@]}"; do
                echo "COST memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "$root/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "K5_COST_DONE $(date -Is)"
