#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
root=build/post64/k4-load-schedule
sha256sum -c results/post64/k4-load-schedule/sources.sha256
sha256sum "$root/fbench.c"
for v in baseline bfirst interleave; do
    sha256sum "$root/$v.c"
    gcc -O3 "$root/fbench.c" "$root/$v.c" -o "$root/bench_$v" -lm -fopenmp
    sha256sum "$root/bench_$v"
done
for v in bfirst interleave; do
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/state_$v" -lm
    gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/$v.c" -o "$root/guard_$v" -lm
    sha256sum "$root/state_$v" "$root/guard_$v"
    for pack in -1 0 1 2 3; do
        echo "K4_LOAD_SCHEDULE_PACK variant=$v mode=$pack"
        OMP_NUM_THREADS=7 CONV_PACKSER="$pack" TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/state_$v"
    done
    echo "K4_LOAD_SCHEDULE_GUARD variant=$v"
    OMP_NUM_THREADS=7 "${run[@]}" "$root/guard_$v"
done
orders=('baseline bfirst interleave' 'bfirst interleave baseline' 'interleave baseline bfirst'
        'interleave bfirst baseline' 'baseline interleave bfirst' 'bfirst baseline interleave')
shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
for round in 0 1 2 3 4 5; do
    read -ra order <<< "${orders[$round]}"
    for memory in DDR HBM; do
        run=(numactl -N "$cpu_node")
        if [[ "$memory" == HBM ]]; then
            (( hbm_node >= 0 )) || continue
            run+=(--preferred="$hbm_node")
        fi
        for shape in "${shapes[@]}"; do
            read -ra args <<< "$shape"
            for v in "${order[@]}"; do
                echo "K4_LOAD_SCHEDULE memory=$memory round=$round variant=$v shape=$shape"
                "${run[@]}" "$root/bench_$v" "${args[@]}" 5
            done
        done
    done
done
echo "K4_LOAD_SCHEDULE_DONE $(date -Is)"
