#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
root=build/v60/release
sha256sum "$root/v59.c" "$root/v60.c" "$root/bench_conv.c"
for variant in v59 v60; do
    gcc -O3 "$root/bench_conv.c" "$root/$variant.c" -o "$root/$variant" -lm -fopenmp
done
sha256sum "$root/v59" "$root/v60"
shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
for round in 0 1 2 3 4 5; do
    order=(v59 v60)
    if (( round % 2 )); then order=(v60 v59); fi
    for memory in DDR HBM; do
        run=(numactl -N "$cpu_node")
        if [[ "$memory" == HBM ]]; then
            (( hbm_node >= 0 )) || continue
            run+=(--preferred="$hbm_node")
        fi
        for shape in "${shapes[@]}"; do
            read -ra args <<< "$shape"
            for variant in "${order[@]}"; do
                echo "V60_RELEASE memory=$memory round=$round variant=$variant shape=$shape"
                "${run[@]}" "$root/$variant" "${args[@]}" 5
            done
        done
    done
done
echo "V60_RELEASE_DONE $(date -Is)"
