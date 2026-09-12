#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE
root=build/v56/experiments/k4-ext
sha256sum "$root/fbench.c" "$root/baseline_poison.c" "$root/k4ext_poison.c" "$root/both_overlap.c"
mkdir -p "$root/disassembly"
for v in baseline k4ext k9align both; do
    sha256sum "$root/$v.c"
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/state_$v" -lm
    echo "K4EXT_STATE variant=$v"
    OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state_$v"
    gcc -O3 -fopenmp -I tools "$root/guard.c" "$root/$v.c" -o "$root/guard_$v" -lm
    OMP_NUM_THREADS=7 "${run[@]}" "$root/guard_$v"
    gcc -O3 -fopenmp "$root/fbench.c" "$root/$v.c" -o "$root/bench_$v" -lm
    objdump -d "$root/bench_$v" > "$root/disassembly/$v.txt"
done
for v in baseline k4ext; do
    echo "POISON_VARIANT $v"
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/${v}_poison.c" -o "$root/poison_state_$v" -lm
    OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/poison_state_$v"
    gcc -O3 -fopenmp -I tools "$root/guard.c" "$root/${v}_poison.c" -o "$root/poison_guard_$v" -lm
    OMP_NUM_THREADS=7 "${run[@]}" "$root/poison_guard_$v"
done
gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/both_overlap.c" -o "$root/overlap" -lm
OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/overlap"
# Williams design: each variant occupies each position and follows each other once.
orders=('baseline k4ext both k9align' 'k4ext k9align baseline both'
        'k9align both k4ext baseline' 'both baseline k9align k4ext')
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
                echo "K4EXT memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "$root/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "K4_EXT_DONE $(date -Is)"
