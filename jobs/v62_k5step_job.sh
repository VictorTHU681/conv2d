#!/usr/bin/env bash
# v62 侦察：v61 逐内核诊断 + K5 计划的续算块长扫描（默认 2 vs 4 vs 8，HBM/DDR 分开看）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/s_cand" -lm
sha256sum "$S/k8ext.c"

shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
echo "=== DIAG per-kind (HBM, v61)"
for args in "${shapes[@]}"; do
    read -ra shape <<< "$args"
    echo "DIAG shape=$args"
    env CONV_ROLL_DIAG=1 "${run[@]}" "$S/s_cand" "${shape[@]}" 3 2>&1 | grep -aE "roll|best"
done

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; cmd+=(--preferred="$hbm_node"); fi
    for round in 1 2 3; do
        order=(def s4 s8)
        (( round == 2 )) && order=(s8 s4 def)
        (( round == 3 )) && order=(s4 def s8)
        for args in '6144 4096 41 41' '4096 6144 39 39'; do
            read -ra shape <<< "$args"
            for v in "${order[@]}"; do
                case "$v" in
                    def) mode=() ;;
                    s4)  mode=(CONV_ROLL_STEP=4) ;;
                    s8)  mode=(CONV_ROLL_STEP=8) ;;
                esac
                printf "K5S memory=%s round=%d variant=%-4s shape=%s " "$memory" "$round" "$v" "$args"
                report=$(env "${mode[@]}" "${cmd[@]}" "$S/s_cand" "${shape[@]}" 5 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V62_K5STEP_DONE $(date -Is)"
