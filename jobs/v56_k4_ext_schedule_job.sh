#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP
root=build/v56/experiments/k4-ext-schedule
sha256sum "$root/fbench.c" "$root/interleaved_poison.c" "$root/interleaved_overlap.c"
mkdir -p "$root/disassembly"
for v in baseline blocked interleaved; do
    sha256sum "$root/$v.c"
    gcc -O3 -fopenmp "$root/fbench.c" "$root/$v.c" -o "$root/bench_$v" -lm
    objdump -d "$root/bench_$v" > "$root/disassembly/$v.txt"
done
gcc -O3 -fopenmp tools/test_v54_state.c "$root/interleaved.c" -o "$root/state" -lm
for mode in -1 0 1 2 3; do
    echo "EXT_SCHEDULE_PACK mode=$mode"
    OMP_NUM_THREADS=7 CONV_PACKSER="$mode" CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state"
done
for suffix in '' '_poison'; do
    echo "EXT_SCHEDULE_GUARD suffix=$suffix"
    gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/interleaved$suffix.c" -o "$root/guard$suffix" -lm
    OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 "${run[@]}" "$root/guard$suffix"
done
gcc -O3 -fopenmp tools/test_v54_state.c "$root/interleaved_poison.c" -o "$root/state_poison" -lm
echo 'EXT_SCHEDULE_POISON'
OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state_poison"
gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/interleaved_overlap.c" -o "$root/overlap" -lm
OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/overlap"
orders=('baseline blocked interleaved' 'blocked interleaved baseline' 'interleaved baseline blocked'
        'interleaved blocked baseline' 'baseline interleaved blocked' 'blocked baseline interleaved')
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
                echo "EXT_SCHEDULE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "$root/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "K4_EXT_SCHEDULE_DONE $(date -Is)"
