#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
variants=(baseline sharekf veckf sharevec)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/fbench.c "build/v56/experiments/coefficient-packing/${v}_phase.c" -o "build/v56/experiments/coefficient-packing/phase_$v" -lm
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for v in "${variants[@]}"; do
            echo "PHASE memory=$memory variant=$v shape=$args"
            CONV_ROLL_DIAG=1 "${run[@]}" "build/v56/experiments/coefficient-packing/phase_$v" "${shape[@]}" 3
        done
    done
done
echo "V56_COEFF_PACK_PHASE_DONE $(date -Is)"
