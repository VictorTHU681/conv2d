#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
for v in baseline k9weave k9split k9both k8planes; do
    sha256sum "build/v56/$v.c" "build/v56/compile_$v"
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '6144 4096 41 41' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for v in baseline k9weave k9split k9both k8planes; do
            echo "PHASE memory=$memory variant=$v shape=$args"
            CONV_ROLL_DIAG=1 "${run[@]}" "build/v56/compile_$v" "${shape[@]}" 3
        done
    done
done
echo "V56_DIAG_DONE $(date -Is)"
