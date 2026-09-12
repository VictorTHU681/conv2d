#!/usr/bin/env bash
# v57 候选1：pairf4 按行长分路（steps>=64 穿插拷贝 + 跳过式 128B 对齐）。
# A/B：merged 基线（v54_stack/candidate.c = 756e1173）vs 新候选（newcand.c）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/candidate.c" -o "$S/g_base" -lm
gcc "${flags[@]}" tools/fbench.c "$S/newcand.c" -o "$S/g_cand" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$S/newcand.c" -o "$S/g_state" -lm
sha256sum "$S/candidate.c" "$S/newcand.c"

echo "=== STATE"
TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/g_state" | tail -1

shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; cmd+=(--preferred="$hbm_node"); fi
    for round in 1 2 3; do
        order=(base cand)
        (( round % 2 == 0 )) && order=(cand base)
        for args in "${shapes[@]}"; do
            read -ra shape <<< "$args"
            for v in "${order[@]}"; do
                printf "GATE memory=%s round=%d variant=%-5s shape=%s " "$memory" "$round" "$v" "$args"
                report=$("${cmd[@]}" "$S/g_$v" "${shape[@]}" 5 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V57_GATE_DONE $(date -Is)"
