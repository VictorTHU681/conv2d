#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE CONV_ROLL_STEP
root=build/v56/experiments/plan-capacity
sha256sum "$root/bench_conv.c" "$root/v55.c" "$root/capacity.c"
gcc -O3 -fopenmp tools/test_v56_plan_threads.c "$root/capacity.c" -o "$root/threads" -lm
for pool in 0 1; do
    echo "CAPACITY_THREAD_POOL $pool"
    CONV_POOL="$pool" TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/threads"
done
gcc -O3 -fopenmp tools/test_v54_state.c "$root/capacity.c" -o "$root/state" -lm
for mode in -1 0 1 2 3; do
    echo "CAPACITY_PACK $mode"
    OMP_NUM_THREADS=7 CONV_PACKSER="$mode" TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/state"
done
gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/capacity.c" -o "$root/guard" -lm
OMP_NUM_THREADS=7 "${run[@]}" "$root/guard"
for v in v55 capacity; do
    gcc -O3 "$root/bench_conv.c" "$root/$v.c" -o "$root/official_$v" -lm -fopenmp
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 0 1 2 3 4 5; do
            if (( round%2==0 )); then order=(v55 capacity); else order=(capacity v55); fi
            for v in "${order[@]}"; do
                echo "CAPACITY_CONFIRM memory=$memory round=$round variant=$v shape=$args"
                report=$("${run[@]}" "$root/official_$v" "${shape[@]}" 5)
                printf '%s\n' "$report"
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "CAPACITY_CONFIRM_DONE $(date -Is)"
