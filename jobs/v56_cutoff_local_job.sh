#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP
root=build/v56/experiments/cutoff-local
sha256sum "$root/fbench.c"
mkdir -p "$root/disassembly"
for v in baseline cutoff local; do
    sha256sum "$root/$v.c"
    gcc -O3 -fopenmp "$root/fbench.c" "$root/$v.c" -o "$root/bench_$v" -lm
    objdump -d "$root/bench_$v" > "$root/disassembly/$v.txt"
done
for v in local; do
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/state_$v" -lm
    for mode in -1 0 1 2 3; do
        echo "LOCAL_PACK variant=$v mode=$mode"
        OMP_NUM_THREADS=7 CONV_PACKSER="$mode" TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state_$v"
    done
    echo "LOCAL_OVERRIDE variant=$v step=1"
    OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state_$v"
    gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/$v.c" -o "$root/guard_$v" -lm
    OMP_NUM_THREADS=7 "${run[@]}" "$root/guard_$v"
    gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/${v}_overlap.c" -o "$root/overlap_$v" -lm
    OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/overlap_$v"
    gcc -O3 -fopenmp tools/test_v56_guided_overlap.c "$root/${v}_overlap.c" -o "$root/guided_$v" -lm
    for mode in -1 0; do
        echo "LOCAL_LONG variant=$v mode=$mode"
        OMP_NUM_THREADS=3 CONV_PACKSER="$mode" TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/guided_$v"
    done
done
orders=('baseline cutoff local' 'cutoff local baseline' 'local baseline cutoff'
        'local cutoff baseline' 'baseline local cutoff' 'cutoff baseline local')
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 0 1 2 3 4 5; do
            read -ra order <<< "${orders[$round]}"
            for v in "${order[@]}"; do
                echo "LOCAL memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "$root/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "CUTOFF_LOCAL_DONE $(date -Is)"
