#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
root=build/post61/k5-events
sha256sum "$root/fbench.c"
for v in baseline clearfirst deferclear; do
    sha256sum "$root/$v.c"
    gcc -O3 -fopenmp "$root/fbench.c" "$root/$v.c" -o "$root/bench_$v" -lm
    sha256sum "$root/bench_$v"
    objdump -d "$root/bench_$v" > "$root/$v.dis"
done
python3 tools/inspect_post61_k5_events.py
for v in clearfirst deferclear; do
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/state_$v" -lm
    for mode in -1 0 1 2 3; do
        echo "K5_EVENTS_PACK variant=$v mode=$mode"
        OMP_NUM_THREADS=7 CONV_PACKSER="$mode" TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/state_$v"
    done
    gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/$v.c" -o "$root/guard_$v" -lm
    OMP_NUM_THREADS=7 "${run[@]}" "$root/guard_$v"
    gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/${v}_overlap.c" -o "$root/overlap_$v" -lm
    OMP_NUM_THREADS=7 TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/overlap_$v"
done
orders=('baseline clearfirst deferclear' 'clearfirst deferclear baseline' 'deferclear baseline clearfirst'
        'deferclear clearfirst baseline' 'baseline deferclear clearfirst' 'clearfirst baseline deferclear')
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
                echo "K5_EVENTS memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "$root/bench_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "K5_EVENTS_SCREEN_DONE $(date -Is)"

for v in baseline clearfirst deferclear; do
    sha256sum "$root/${v}_profile.c"
    gcc -O3 -fopenmp "$root/fbench.c" "$root/${v}_profile.c" -o "$root/profile_$v" -lm
    sha256sum "$root/profile_$v"
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for round in 0 1 2 3 4 5; do
        read -ra order <<< "${orders[$round]}"
        for v in "${order[@]}"; do
            echo "K5_EVENTS_PROFILE memory=$memory round=$round variant=$v shape=6144 4096 41 41"
            CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile_$v" 6144 4096 41 41 5
        done
    done
done
echo "K5_EVENTS_DONE $(date -Is)"
