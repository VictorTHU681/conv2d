#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
for v in phase nine_reload_phase nine_plane_reload_phase nine_plane_ext_phase; do
    gcc "${flags[@]}" tools/fbench.c "build/v55/$v.c" -o "build/v55/dg9_$v" -lm
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '6144 4096 41 41' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for v in phase nine_reload_phase nine_plane_reload_phase nine_plane_ext_phase; do
            echo "PHASE memory=$memory variant=$v shape=$args"
            CONV_ROLL_DIAG=1 "${run[@]}" "build/v55/dg9_$v" "${shape[@]}" 3
        done
    done
done
echo "NINE_DIAG_DONE $(date -Is)"
