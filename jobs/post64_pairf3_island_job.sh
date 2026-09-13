#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
root=build/post64/pairf3-island
candidate=island
sha256sum -c results/post64/pairf3-island/sources.sha256
sha256sum "$root/bench_conv.c"
for v in baseline u4 "$candidate"; do
    sha256sum "$root/$v.c"
    gcc -O3 "$root/bench_conv.c" "$root/$v.c" -o "$root/official_$v" -lm -fopenmp
    sha256sum "$root/official_$v"
done
gcc -O3 -fopenmp tools/test_v54_state.c "$root/island.c" -o "$root/state_island" -lm
gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/island.c" -o "$root/guard_island" -lm
gcc -O3 -fopenmp -I tools tools/test_post64_pairf3_suffix_guard.c "$root/island.c" -o "$root/suffix_guard_island" -lm
sha256sum "$root/state_island" "$root/guard_island" "$root/suffix_guard_island"
for pack in -1 0 1 2 3; do
    echo "PAIRF3_PACK mode=$pack"
    OMP_NUM_THREADS=7 CONV_PACKSER="$pack" TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/state_island"
done
OMP_NUM_THREADS=7 "${run[@]}" "$root/guard_island"
OMP_NUM_THREADS=7 CONV_NF=3 "${run[@]}" "$root/guard_island"
OMP_NUM_THREADS=7 CONV_NF=3 "${run[@]}" "$root/suffix_guard_island"
orders=('baseline u4 island' 'u4 island baseline' 'island baseline u4' 'island u4 baseline' 'baseline island u4' 'u4 baseline island')
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
                echo "PAIRF3_ISLAND memory=$memory round=$round variant=$v shape=$shape"
                "${run[@]}" "$root/official_$v" "${args[@]}" 5
            done
        done
    done
done
echo "PAIRF3_ISLAND_DONE $(date -Is)"
