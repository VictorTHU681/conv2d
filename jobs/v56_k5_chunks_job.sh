#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE
root=build/v56/experiments/k5-chunks
sha256sum "$root/candidate.c" "$root/fbench.c" "$root/candidate_overlap.c"
gcc -O3 -fopenmp "$root/fbench.c" "$root/candidate.c" -o "$root/bench" -lm
gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/candidate_overlap.c" -o "$root/overlap" -lm
for step in 2 4 8 16; do
    echo "CHUNK_OWNERSHIP step=$step"
    OMP_NUM_THREADS=7 CONV_ROLL_STEP="$step" TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/overlap"
done
orders=('8 4 16 2' '4 2 8 16' '2 16 4 8' '16 8 2 4')
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
            for step in "${order[@]}"; do
                echo "CHUNK memory=$memory round=$round step=$step shape=$args"
                CONV_ROLL_STEP="$step" "${run[@]}" "$root/bench" "${shape[@]}" 5
            done
        done
    done
done
echo "K5_CHUNKS_DONE $(date -Is)"
