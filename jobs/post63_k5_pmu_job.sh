#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
root=build/post63/k5-pmu
sha256sum "$root/candidate.c" "$root/pmu.c" "$root/fbench.c"
gcc -O3 "$root/fbench.c" "$root/pmu.c" -o "$root/bench" -lm -fopenmp
gcc -O3 -fopenmp tools/test_v54_state.c "$root/candidate.c" -o "$root/state" -lm
gcc -O3 -fopenmp -I tools tools/test_v56_planar_full_guard.c "$root/candidate.c" -o "$root/guard" -lm
sha256sum "$root/bench" "$root/state" "$root/guard"
for mode in 0 1 2; do
    echo "PMU_STATE mode=$mode"
    CONV_K5_ORDER="$mode" CONV_K5_PMU=1 OMP_NUM_THREADS=7 TEST_SIGNED=1 TEST_BITWISE=1 "${run[@]}" "$root/state"
    echo "PMU_GUARD mode=$mode"
    CONV_K5_ORDER="$mode" CONV_K5_PMU=1 OMP_NUM_THREADS=7 "${run[@]}" "$root/guard"
done
orders=('0 1 2' '1 2 0' '2 0 1' '2 1 0' '0 2 1' '1 0 2')
for round in 0 1 2 3 4 5; do
    read -ra order <<< "${orders[$round]}"
    for memory in DDR HBM; do
        run=(numactl -N "$cpu_node")
        if [[ "$memory" == HBM ]]; then
            (( hbm_node >= 0 )) || continue
            run+=(--preferred="$hbm_node")
        fi
        for mode in "${order[@]}"; do
            echo "PMU_COMPARE memory=$memory round=$round mode=$mode shape=6144 4096 41 41"
            CONV_K5_ORDER="$mode" CONV_K5_PMU=1 CONV_ROLL_DIAG=1 "${run[@]}" "$root/bench" 6144 4096 41 41 5
        done
    done
done
echo 'PMU_COMPARE_DONE'
for round in 0 1 2 3 4 5; do
    if (( round%2 )); then controls=(1 0); else controls=(0 1); fi
    for memory in DDR HBM; do
        run=(numactl -N "$cpu_node")
        if [[ "$memory" == HBM ]]; then
            (( hbm_node >= 0 )) || continue
            run+=(--preferred="$hbm_node")
        fi
        for enabled in "${controls[@]}"; do
            echo "PMU_OVERHEAD memory=$memory round=$round enabled=$enabled shape=6144 4096 41 41"
            CONV_K5_ORDER=0 CONV_K5_PMU="$enabled" CONV_ROLL_DIAG=1 "${run[@]}" "$root/bench" 6144 4096 41 41 5
        done
    done
done
echo "PMU_DONE $(date -Is)"
