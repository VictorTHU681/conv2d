#!/usr/bin/env bash
# v55 第三轮：K4/8×2/single 加速后的代价权重重扫（划分均衡）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/candidate.c" -o "$S/w4_cand" -lm
sha256sum "$S/candidate.c"

shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        cmd+=(--preferred="$hbm_node")
    fi
    for round in 1 2; do
        order=(base w110 w116 w105 w110s w116s)
        (( round == 2 )) && order=(w116s w110s w105 w116 w110 base)
        for args in "${shapes[@]}"; do
            read -ra shape <<< "$args"
            for variant in "${order[@]}"; do
                case "$variant" in
                    base)  mode=() ;;
                    w105)  mode=(CONV_ROLL_W4=105) ;;
                    w110)  mode=(CONV_ROLL_W4=110) ;;
                    w116)  mode=(CONV_ROLL_W4=116) ;;
                    w110s) mode=(CONV_ROLL_W4=110 CONV_ROLL_W8=102 CONV_ROLL_W16=101) ;;
                    w116s) mode=(CONV_ROLL_W4=116 CONV_ROLL_W8=102 CONV_ROLL_W16=101) ;;
                esac
                printf "W4 memory=%s round=%d variant=%-6s shape=%s " "$memory" "$round" "$variant" "$args"
                report=$(env "${mode[@]}" "${cmd[@]}" "$S/w4_cand" "${shape[@]}" 5 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V55_W4_DONE $(date -Is)"
