#!/usr/bin/env bash
# v63 侦察：K9 静态划分权重扫描（实测 K9/pair 周期比 ~1.10，现值 140 疑高）。
# k81 扫 W9；k41 顺带复核 W4（K5 引入后 123 是否仍优）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/s_w9" -lm
sha256sum "$S/k8ext.c"

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; cmd+=(--preferred="$hbm_node"); fi
    for round in 1 2 3; do
        w9s=(140 125 115 108)
        (( round == 2 )) && w9s=(108 115 125 140)
        (( round == 3 )) && w9s=(115 140 108 125)
        for w9 in "${w9s[@]}"; do
            printf "W9 memory=%s round=%d w9=%-3s shape=6390 4256 81 81 " "$memory" "$round" "$w9"
            report=$(env CONV_ROLL_W9=$w9 "${cmd[@]}" "$S/s_w9" 6390 4256 81 81 5 2>&1)
            printf '%s\n' "$report" | tail -1
            [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
        done
        w4s=(123 112)
        (( round == 2 )) && w4s=(112 123)
        for w4 in "${w4s[@]}"; do
            printf "W4 memory=%s round=%d w4=%-3s shape=6144 4096 41 41 " "$memory" "$round" "$w4"
            report=$(env CONV_ROLL_W4=$w4 "${cmd[@]}" "$S/s_w9" 6144 4096 41 41 5 2>&1)
            printf '%s\n' "$report" | tail -1
            [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
        done
    done
done
echo "V63_W9_DONE $(date -Is)"
