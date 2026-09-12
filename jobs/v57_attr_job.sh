#!/usr/bin/env bash
# v57 归因：跳段诊断变体（结果错误、仅时序）量化 pairf4 事件 / K4 拷贝+事件 / K9 拷贝+事件的真实占比。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v57
for v in base pf4_noev k4_noev k4_nocopy k9_noev k9_nocopy; do
    gcc "${flags[@]}" tools/fbench.c "$S/$v.c" -o "$S/fb_$v" -lm
done
sha256sum "$S"/base.c | head -1

# 仅时序：诊断变体哈希必然 FAIL，忽略退出码，收集每轮 run 行
for memory in HBM; do
    cmd=(numactl -N "$cpu_node")
    (( hbm_node >= 0 )) && cmd+=(--preferred="$hbm_node")
    for round in 1 2 3; do
        for args in '4096 6144 39 39' '4256 6390 55 55' '6390 4256 81 81'; do
            read -ra shape <<< "$args"
            for v in base pf4_noev k4_noev k4_nocopy k9_noev k9_nocopy; do
                echo "ATTR round=$round variant=$v shape=$args"
                env FBENCH_FORCE=1 "${cmd[@]}" "$S/fb_$v" "${shape[@]}" 4 2>&1 | grep -aE "run[0-9]|best" || true
            done
        done
    done
done
echo "V57_ATTR_DONE $(date -Is)"
