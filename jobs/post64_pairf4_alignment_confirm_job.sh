#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
root=build/post64/pairf4-alignment
candidate=aligned
sha256sum -c results/post64/pairf4-alignment/official_sources.sha256
sha256sum "$root/bench_conv.c"
for v in baseline "$candidate"; do
    sha256sum "$root/$v.c"
    gcc -O3 "$root/bench_conv.c" "$root/$v.c" -o "$root/official_$v" -lm -fopenmp
    sha256sum "$root/official_$v"
done
orders=("baseline $candidate" "$candidate baseline" "baseline $candidate" "$candidate baseline" "baseline $candidate" "$candidate baseline")
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
                echo "PAIRF4_ALIGN_CONFIRM memory=$memory round=$round variant=$v shape=$shape"
                "${run[@]}" "$root/official_$v" "${args[@]}" 5
            done
        done
    done
done
echo "PAIRF4_ALIGN_CONFIRM_DONE $(date -Is)"
