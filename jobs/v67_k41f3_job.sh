#!/usr/bin/env bash
# v67 侦察：k41 形态实验 35+K5(5) vs 34+k8(6)（CONV_K41F3=1）。
# 槽位算术约打平；nf3 先例表明时延效应可翻盘。k81 顺带验证 rem9 路径未受影响（其 rem=17）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/s_f3" -lm
sha256sum "$S/k8ext.c"

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; cmd+=(--preferred="$hbm_node"); fi
    for round in 1 2 3; do
        order=(def f3)
        (( round == 2 )) && order=(f3 def)
        for v in "${order[@]}"; do
            case "$v" in def) mode=() ;; f3) mode=(CONV_K41F3=1) ;; esac
            printf "K41F memory=%s round=%d variant=%-3s shape=6144 4096 41 41 " "$memory" "$round" "$v"
            report=$(env "${mode[@]}" "${cmd[@]}" "$S/s_f3" 6144 4096 41 41 4 2>&1)
            printf '%s\n' "$report" | tail -1
            [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
        done
    done
done
echo "V67_K41F3_DONE $(date -Is)"
