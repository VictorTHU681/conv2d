#!/usr/bin/env bash
# v66 侦察 A：v65 上 k39 的 NF 配对复检（pairf3 展开后 nf3 路径可能反超 nf4 默认）。
# 证据线索：1594156 nf3-k39 +0.84%、1591028 +1.48%（均单次非配对）。
# 同节点交替、3 轮 × 5 计时、HBM/DDR 分开。附带 k55 的 NF=4 反向确认（auto=3 应保持）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/s_nf" -lm
sha256sum "$S/k8ext.c"

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; cmd+=(--preferred="$hbm_node"); fi
    for round in 1 2 3; do
        order=(auto nf3)
        (( round == 2 )) && order=(nf3 auto)
        for v in "${order[@]}"; do
            case "$v" in auto) mode=(CONV_NF=0) ;; nf3) mode=(CONV_NF=3) ;; esac
            printf "NF memory=%s round=%d variant=%-4s shape=4096 6144 39 39 " "$memory" "$round" "$v"
            report=$(env "${mode[@]}" "${cmd[@]}" "$S/s_nf" 4096 6144 39 39 5 2>&1)
            printf '%s\n' "$report" | tail -1
            [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
        done
        for v in "${order[@]}"; do
            case "$v" in auto) mode=(CONV_NF=0) ;; nf3) mode=(CONV_NF=4) ;; esac   # k55: auto(3) vs 强制 4
            printf "NF55 memory=%s round=%d variant=%-4s shape=4256 6390 55 55 " "$memory" "$round" "$v"
            report=$(env "${mode[@]}" "${cmd[@]}" "$S/s_nf" 4256 6390 55 55 5 2>&1)
            printf '%s\n' "$report" | tail -1
            [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
        done
    done
done
echo "V66_NF_DONE $(date -Is)"
