#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/planar-fix-full
for v in baseline fixed mergedfixed; do
    gcc -O3 -fopenmp tools/test_v56_planar_fix_audit.c "$root/${v}_audit.c" -o "$root/audit_$v" -lm
    expected=(); [[ "$v" == baseline ]] && expected=(AUDIT_EXPECT_OVERREAD=1)
    echo "PLANAR_FIX_AUDIT $v"
    env "${expected[@]}" OMP_NUM_THREADS=7 "${run[@]}" "$root/audit_$v"
done
for v in fixed mergedfixed; do
    gcc -O3 -fopenmp tools/test_v56_planar_full_guard.c "$root/$v.c" -o "$root/guard_$v" -lm
    echo "PLANAR_GUARD $v"
    OMP_NUM_THREADS=7 "${run[@]}" "$root/guard_$v"
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/state_$v" -lm
    for mode in default 0 1 2 3; do
        knobs=(); [[ "$mode" != default ]] && knobs=(CONV_PACKSER="$mode")
        # Local source has only serial/parallel modes; 2/3 are upstream additions.
        if [[ "$v" == fixed && ( "$mode" == 2 || "$mode" == 3 ) ]]; then continue; fi
        echo "PLANAR_STATE $v pack=$mode"
        env "${knobs[@]}" OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$root/state_$v"
    done
done
variants=(baseline upstream fixed mergedfixed)
for v in "${variants[@]}"; do
    sha256sum "$root/$v.c"
    gcc -O3 -fopenmp tools/fbench.c "$root/$v.c" -o "$root/bench_$v" -lm
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
            if (( round % 2 == 0 )); then order=(mergedfixed fixed upstream baseline); fi
            for v in "${order[@]}"; do
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "$root/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "V56_PLANAR_FIX_FULL_DONE $(date -Is)"
