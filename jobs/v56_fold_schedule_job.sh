#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP
root=build/v56/experiments/fold-schedule
sha256sum "$root/fbench.c"
for v in baseline f4 f34; do
    sha256sum "$root/$v.c"
    gcc -O3 -fopenmp "$root/fbench.c" "$root/$v.c" -o "$root/bench_$v" -lm
    objdump -d "$root/bench_$v" > "$root/$v.dis"
done
for v in f4 f34; do
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/state_$v" -lm
    for mode in -1 0 1 2 3; do
        echo "FOLD_PACK variant=$v mode=$mode"
        OMP_NUM_THREADS=7 CONV_PACKSER="$mode" TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/state_$v"
    done
    gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/$v.c" -o "$root/guard_$v" -lm
    OMP_NUM_THREADS=7 "${run[@]}" "$root/guard_$v"
    gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/${v}_overlap.c" -o "$root/overlap_$v" -lm
    OMP_NUM_THREADS=7 TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/overlap_$v"
done
orders=('baseline f4 f34' 'f4 f34 baseline' 'f34 baseline f4'
        'f34 f4 baseline' 'baseline f34 f4' 'f4 baseline f34')
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
                echo "FOLD memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "$root/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "FOLD_SCHEDULE_DONE $(date -Is)"
