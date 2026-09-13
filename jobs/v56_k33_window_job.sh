#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
variants=(baseline outline unroll4 ext4 tbl4 tbl8)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/fbench.c "build/v56/experiments/k33-window/$v.c" -o "build/v56/experiments/k33-window/bench_$v" -lm
    sha256sum "build/v56/experiments/k33-window/$v.c"
    objdump -d --disassemble=roll_worker "build/v56/experiments/k33-window/bench_$v" > "results/v56/experiments/k33-window/disas_$v.txt"
    objdump -d --disassemble=k16pairf "build/v56/experiments/k33-window/bench_$v" > "results/v56/experiments/k33-window/pairf_$v.txt"
    if [[ "$v" != baseline ]]; then
        gcc "${flags[@]}" tools/test_v54_state.c "build/v56/experiments/k33-window/$v.c" -o "build/v56/experiments/k33-window/state_$v" -lm
        echo "STATE_BEGIN $v"
        OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "build/v56/experiments/k33-window/state_$v"
        gcc "${flags[@]}" tools/test_v56_k33_window.c "build/v56/experiments/k33-window/$v.c" -o "build/v56/experiments/k33-window/extended_$v" -lm
        OMP_NUM_THREADS=2 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "build/v56/experiments/k33-window/extended_$v"
    fi
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 1 2 3; do
            order=("${variants[@]}")
            if (( round % 2 == 0 )); then order=(tbl8 tbl4 ext4 unroll4 outline baseline); fi
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "build/v56/experiments/k33-window/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "V56_K33_WINDOW_DONE $(date -Is)"
