#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
root=build/post64/k4-scalar
sha256sum "$root/fbench.c"
sha256sum -c results/post64/k4-scalar/profile_sources.sha256
for v in baseline bits; do
    sha256sum "$root/${v}_profile.c"
    gcc -O3 "$root/fbench.c" "$root/${v}_profile.c" -o "$root/profile_$v" -lm -fopenmp
    sha256sum "$root/profile_$v"
done
orders=('baseline bits' 'bits baseline' 'baseline bits' 'bits baseline' 'baseline bits' 'bits baseline')
shapes=('4096 6144 39 39' '4256 6390 55 55')
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
                echo "K4_PROFILE memory=$memory round=$round variant=$v shape=$shape"
                CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile_$v" "${args[@]}" 5
            done
        done
    done
done
echo "K4_PROFILE_DONE $(date -Is)"
