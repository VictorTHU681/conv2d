#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE SCREEN_HASH_EACH
root=build/post64/hash-between
sha256sum -c results/post64/hash-between/sources.sha256
for v in baseline all; do
    gcc -O3 "$root/driver.c" "$root/$v.c" -o "$root/bench_$v" -lm -fopenmp
    sha256sum "$root/$v.c" "$root/bench_$v"
done
sha256sum "$root/driver.c"
# Each condition occupies each position twice; ordered adjacent pairs also
# occur twice across eight Williams-design orders. Same binary per variant.
orders=('0 1 3 2' '1 2 0 3' '2 3 1 0' '3 0 2 1'
        '2 3 1 0' '3 0 2 1' '0 1 3 2' '1 2 0 3')
variants=(baseline all baseline all)
hash_modes=(1 1 0 0)
shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55')
for round in 0 1 2 3 4 5 6 7; do
    read -ra order <<< "${orders[$round]}"
    for memory in DDR HBM; do
        run=(numactl -N "$cpu_node")
        if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; run+=(--preferred="$hbm_node"); fi
        for shape in "${shapes[@]}"; do
            read -ra args <<< "$shape"
            for condition in "${order[@]}"; do
                v=${variants[$condition]}; h=${hash_modes[$condition]}
                echo "HASH_BETWEEN memory=$memory round=$round condition=$condition variant=$v hash_each=$h shape=$shape"
                SCREEN_HASH_EACH=$h "${run[@]}" "$root/bench_$v" "${args[@]}" 5
            done
        done
    done
done
echo "HASH_BETWEEN_DONE $(date -Is)"
