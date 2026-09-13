#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/k33-window
memory=${CONV_TEST_MEMORY:?set DDR or HBM}
run=(numactl -N "$cpu_node")
if [[ "$memory" == HBM ]]; then
    (( hbm_node >= 0 )) || { echo 'HBM unavailable'; exit 2; }
    run+=(--preferred="$hbm_node")
elif [[ "$memory" != DDR ]]; then exit 2; fi
for v in baseline outline unroll4; do
    gcc -O3 bench_conv.c "$root/$v.c" -o "$root/off_${memory}_$v" -lm -fopenmp
    sha256sum "$root/$v.c"
done
# All six permutations balance position and the six ordered predecessor pairs.
orders=('baseline outline unroll4' 'outline unroll4 baseline' 'unroll4 baseline outline'
        'unroll4 outline baseline' 'baseline unroll4 outline' 'outline baseline unroll4')
for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    for round in 0 1 2 3 4 5; do
        read -ra order <<< "${orders[$round]}"
        for v in "${order[@]}"; do
            echo "OFFICIAL memory=$memory round=$round variant=$v shape=$args"
            report=$("${run[@]}" "$root/off_${memory}_$v" "${shape[@]}" 5)
            printf '%s\n' "$report"
            [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
        done
    done
done
echo "K33_UNROLL_OFFICIAL_DONE memory=$memory $(date -Is)"
