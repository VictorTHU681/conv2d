#!/usr/bin/env bash
# v66 侦察 B：v62/v64/v65 改变了 K5 循环时序，重扫 k41 的续算块长与 W4 权重（旧最优基于 v61 测定）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/s_k5t" -lm
sha256sum "$S/k8ext.c"

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; cmd+=(--preferred="$hbm_node"); fi
    for round in 1 2 3; do
        vs=(def s4 s8 w115 w119)
        (( round == 2 )) && vs=(w119 w115 s8 s4 def)
        (( round == 3 )) && vs=(s4 def w115 s8 w119)
        for v in "${vs[@]}"; do
            case "$v" in
                def)  mode=() ;;
                s4)   mode=(CONV_ROLL_STEP=4) ;;
                s8)   mode=(CONV_ROLL_STEP=8) ;;
                w115) mode=(CONV_ROLL_W4=115) ;;
                w119) mode=(CONV_ROLL_W4=119) ;;
            esac
            printf "K5T memory=%s round=%d variant=%-5s shape=6144 4096 41 41 " "$memory" "$round" "$v"
            report=$(env "${mode[@]}" "${cmd[@]}" "$S/s_k5t" 6144 4096 41 41 5 2>&1)
            printf '%s\n' "$report" | tail -1
            [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
        done
    done
done
echo "V66_K5T_DONE $(date -Is)"
