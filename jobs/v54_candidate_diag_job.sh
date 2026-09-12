#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"
for v in phase candidatephase; do
    gcc "${flags[@]}" tools/fbench.c "build/v54/$v.c" -o "build/v54/dg_$v" -lm
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for v in phase candidatephase; do
            echo "PHASE memory=$memory variant=$v shape=$args"
            CONV_ROLL_DIAG=1 "${run[@]}" "build/v54/dg_$v" "${shape[@]}" 3
        done
    done
done
echo "CANDIDATE_DIAG_DONE $(date -Is)"
