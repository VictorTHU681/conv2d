#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
root=build/post63/k5-prefix
sha256sum "$root/fbench.c" "$root/bench_conv.c"
for v in baseline exact legacy; do
    sha256sum "$root/$v.c" "$root/${v}_profile.c"
    gcc -O3 "$root/fbench.c" "$root/$v.c" -o "$root/bench_$v" -lm -fopenmp
    gcc -O3 "$root/fbench.c" "$root/${v}_profile.c" -o "$root/profile_$v" -lm -fopenmp
    sha256sum "$root/bench_$v" "$root/profile_$v"
done
for v in baseline exact; do
    sha256sum "$root/${v}_audit.c" "$root/${v}_overlap.c"
    gcc -O3 -fopenmp tools/test_v54_state.c "$root/$v.c" -o "$root/state_$v" -lm
    gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/$v.c" -o "$root/guard_$v" -lm
    gcc -O3 -fopenmp -DK5_INPUT_AUDIT tools/test_v56_k5_triplet.c "$root/${v}_audit.c" -o "$root/extended_$v" -lm
    gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/${v}_overlap.c" -o "$root/ownership_$v" -lm
    for pack in -1 0 1 2 3; do
        echo "K5_COMPOSE_PACK variant=$v mode=$pack"
        OMP_NUM_THREADS=7 CONV_PACKSER="$pack" TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/state_$v"
    done
    echo "K5_COMPOSE_GUARD variant=$v"
    OMP_NUM_THREADS=7 "${run[@]}" "$root/guard_$v"
    echo "K5_COMPOSE_EXTENDED variant=$v"
    OMP_NUM_THREADS=7 TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/extended_$v"
    echo "K5_COMPOSE_OWNERSHIP variant=$v"
    OMP_NUM_THREADS=7 TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/ownership_$v"
done
orders=('baseline exact legacy' 'exact legacy baseline' 'legacy baseline exact'
        'legacy exact baseline' 'baseline legacy exact' 'exact baseline legacy')
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
                echo "K5_COMPOSE memory=$memory round=$round variant=$v shape=$shape"
                "${run[@]}" "$root/bench_$v" "${args[@]}" 5
            done
        done
    done
done
echo "K5_COMPOSE_SCREEN_DONE $(date -Is)"
for round in 0 1 2 3 4 5; do
    read -ra order <<< "${orders[$round]}"
    for memory in DDR HBM; do
        run=(numactl -N "$cpu_node")
        if [[ "$memory" == HBM ]]; then
            (( hbm_node >= 0 )) || continue
            run+=(--preferred="$hbm_node")
        fi
        for v in "${order[@]}"; do
            echo "K5_COMPOSE_PROFILE memory=$memory round=$round variant=$v shape=6144 4096 41 41"
            CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile_$v" 6144 4096 41 41 5
        done
    done
done
echo "K5_COMPOSE_DONE $(date -Is)"
