#!/usr/bin/env bash
# v63 侦察：非 K5 计划的续算块长上探（8 默认 → 12/16/24；恢复+保存 ~1-1.8%/调用，块长翻倍省一半领取）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/s_st" -lm
sha256sum "$S/k8ext.c"

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; cmd+=(--preferred="$hbm_node"); fi
    for round in 1 2 3; do
        steps=(8 12 16 24)
        (( round == 2 )) && steps=(24 16 12 8)
        (( round == 3 )) && steps=(16 8 24 12)
        for args in '4096 6144 39 39' '4256 6390 55 55' '6390 4256 81 81'; do
            read -ra shape <<< "$args"
            for st in "${steps[@]}"; do
                printf "ST memory=%s round=%d st=%-2s shape=%s " "$memory" "$round" "$st" "$args"
                report=$(env CONV_ROLL_STEP=$st "${cmd[@]}" "$S/s_st" "${shape[@]}" 5 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V63_STEP_DONE $(date -Is)"
