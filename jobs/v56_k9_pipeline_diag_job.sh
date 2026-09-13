#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
variants=(baseline unroll2 pipeline2)
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/fbench.c "build/v56/experiments/k9-pipeline/$v.c" -o "build/v56/experiments/k9-pipeline/diag_$v" -lm
    objdump -d --disassemble=k8f "build/v56/experiments/k9-pipeline/diag_$v" > "results/v56/experiments/k9-pipeline/disas_$v.txt"
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for v in "${variants[@]}"; do
        echo "PHASE memory=$memory variant=$v shape=6390 4256 81 81"
        CONV_ROLL_DIAG=1 "${run[@]}" "build/v56/experiments/k9-pipeline/diag_$v" 6390 4256 81 81 3
    done
done
echo "V56_K9_PIPELINE_DIAG_DONE $(date -Is)"
