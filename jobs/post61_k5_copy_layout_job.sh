#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
root=build/post61/k5-copy-layout
sha256sum "$root/candidate.c" "$root/fbench.c" "$root/candidate_audit.c" "$root/candidate_overlap.c" "$root/candidate_profile.c"
gcc -O3 -fopenmp "$root/fbench.c" "$root/candidate.c" -o "$root/bench" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$root/candidate.c" -o "$root/state" -lm
gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/candidate.c" -o "$root/guard" -lm
gcc -O3 -fopenmp -DK5_INPUT_AUDIT tools/test_v56_k5_triplet.c "$root/candidate_audit.c" -o "$root/extended" -lm
gcc -O3 -fopenmp tools/test_v56_output_overlap.c "$root/candidate_overlap.c" -o "$root/ownership" -lm
sha256sum "$root/bench"
names=(baseline exact triples)
for setting in 0 1 2; do
    export CONV_K5_COPY="$setting"
    v=${names[$setting]}
    for pack in -1 0 1 2 3; do
        echo "K5_COPY_PACK variant=$v mode=$pack"
        OMP_NUM_THREADS=7 CONV_PACKSER="$pack" TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/state"
    done
    echo "K5_COPY_GUARD variant=$v"
    OMP_NUM_THREADS=7 "${run[@]}" "$root/guard"
    echo "K5_COPY_EXTENDED variant=$v"
    OMP_NUM_THREADS=7 TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/extended"
    echo "K5_COPY_OWNERSHIP variant=$v"
    OMP_NUM_THREADS=7 TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/ownership"
done
orders=('0 1 2' '1 2 0' '2 0 1' '2 1 0' '0 2 1' '1 0 2')
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for shape in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra args <<< "$shape"
        for round in 0 1 2 3 4 5; do
            read -ra order <<< "${orders[$round]}"
            for setting in "${order[@]}"; do
                echo "K5_COPY memory=$memory round=$round variant=${names[$setting]} shape=$shape"
                CONV_K5_COPY="$setting" "${run[@]}" "$root/bench" "${args[@]}" 5
            done
        done
    done
done
echo "K5_COPY_SCREEN_DONE $(date -Is)"
gcc -O3 -fopenmp "$root/fbench.c" "$root/candidate_profile.c" -o "$root/profile" -lm
sha256sum "$root/profile"
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for round in 0 1 2 3 4 5; do
        read -ra order <<< "${orders[$round]}"
        for setting in "${order[@]}"; do
            echo "K5_COPY_PROFILE memory=$memory round=$round variant=${names[$setting]} shape=6144 4096 41 41"
            CONV_K5_COPY="$setting" CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile" 6144 4096 41 41 5
        done
    done
done
echo "K5_COPY_DONE $(date -Is)"
