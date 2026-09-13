#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP
root=build/v56/experiments/f3-anchor
sha256sum "$root/fbench.c"
mkdir -p "$root/disassembly"
for v in baseline phase baseline_anchor phase_anchor; do
    sha256sum "$root/$v.c"
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/state_$v" -lm
    echo "ANCHOR_STATE variant=$v"
    OMP_NUM_THREADS=7 CONV_ROLL_STEP=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state_$v"
    gcc -O3 -fopenmp "$root/fbench.c" "$root/$v.c" -o "$root/bench_$v" -lm
    objdump -d "$root/bench_$v" > "$root/disassembly/$v.txt"
done
orders=('baseline phase phase_anchor baseline_anchor' 'phase baseline_anchor baseline phase_anchor'
        'baseline_anchor phase_anchor phase baseline' 'phase_anchor baseline baseline_anchor phase')
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
                echo "ANCHOR memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "$root/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "F3_ANCHOR_DONE $(date -Is)"
