#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
unset FBENCH_FORCE
root=build/v56/experiments/upstream-gate
mkdir -p "$root/disassembly"
for v in baseline merged short128; do
    sha256sum "$root/$v.c"
    gcc -O3 -fopenmp tools/fbench.c "$root/$v.c" -o "$root/screen_$v" -lm
    objdump -d --disassemble=roll_worker "$root/screen_$v" > "$root/disassembly/screen_$v.txt"
done
orders=('baseline merged short128' 'merged short128 baseline' 'short128 baseline merged'
        'short128 merged baseline' 'baseline short128 merged' 'merged baseline short128')
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
                echo "MEASURE memory=$memory round=$round variant=$v shape=$args"
                "${run[@]}" "$root/screen_$v" "${shape[@]}" 5
            done
        done
    done
done
echo "UPSTREAM_SHORTALIGN_DONE $(date -Is)"
