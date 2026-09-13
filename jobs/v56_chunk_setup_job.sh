#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP
root=build/v56/experiments/chunk-setup
sha256sum "$root/fbench.c" "$root/both_overlap.c"
mkdir -p "$root/disassembly"
for v in baseline phase carry4 both; do
    sha256sum "$root/$v.c"
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/state_$v" -lm
    echo "SETUP_STATE variant=$v"
    OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state_$v"
    gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/$v.c" -o "$root/guard_$v" -lm
    OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 "${run[@]}" "$root/guard_$v"
    gcc -O3 -fopenmp "$root/fbench.c" "$root/$v.c" -o "$root/bench_$v" -lm
    objdump -d "$root/bench_$v" > "$root/disassembly/$v.txt"
done
for mode in 0 1 2 3; do
    echo "SETUP_PACK mode=$mode"
    OMP_NUM_THREADS=7 CONV_PACKSER="$mode" CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state_both"
done
gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/both_overlap.c" -o "$root/overlap" -lm
OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/overlap"
orders=('baseline phase both carry4' 'phase carry4 baseline both'
        'carry4 both phase baseline' 'both baseline carry4 phase')
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
                echo "SETUP memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "$root/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "CHUNK_SETUP_DONE $(date -Is)"
