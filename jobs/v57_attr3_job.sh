#!/usr/bin/env bash
# v57 归因第三轮：pair 族拷贝 + k41/k55 事件（诊断变体，FBENCH_FORCE 仅时序）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v57
for v in base pf4_nocopy pf1_noev pf3_noev sf2_noev k8_nocopy; do
    gcc "${flags[@]}" tools/fbench.c "$S/$v.c" -o "$S/a3_$v" -lm
done

for memory in HBM; do
    cmd=(numactl -N "$cpu_node")
    (( hbm_node >= 0 )) && cmd+=(--preferred="$hbm_node")
    for round in 1 2 3; do
        for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
            read -ra shape <<< "$args"
            for v in base pf4_nocopy pf1_noev pf3_noev sf2_noev k8_nocopy; do
                echo "A3 round=$round variant=$v shape=$args"
                env FBENCH_FORCE=1 "${cmd[@]}" "$S/a3_$v" "${shape[@]}" 4 2>&1 | grep -aE "best" || true
            done
        done
    done
done
echo "V57_ATTR3_DONE $(date -Is)"
