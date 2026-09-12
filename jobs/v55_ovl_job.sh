#!/usr/bin/env bash
# v55 候选2：行拷贝穿插进步循环（OVL）+ K4 输出预取。位精确 → 逐内核周期 → 同节点 A/B。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/upstream.c" -o "$S/ovl_up" -lm
gcc "${flags[@]}" tools/fbench.c "$S/candidate.c" -o "$S/ovl_cand" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$S/candidate.c" -o "$S/ovl_state" -lm
sha256sum "$S/upstream.c" "$S/candidate.c"

echo "=== STATE default"
TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/ovl_state" | tail -1
echo "=== STATE step4"
CONV_ROLL_STEP=4 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/ovl_state" | tail -1

shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')

echo "=== DIAG per-kind cycles (HBM, candidate)"
for args in "${shapes[@]}"; do
    read -ra shape <<< "$args"
    echo "DIAG shape=$args"
    env CONV_ROLL_DIAG=1 "${run[@]}" "$S/ovl_cand" "${shape[@]}" 3 2>&1 | grep -aE "roll|best"
done

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        cmd+=(--preferred="$hbm_node")
    fi
    for round in 1 2 3; do
        order=(up cand)
        (( round % 2 == 0 )) && order=(cand up)
        for args in "${shapes[@]}"; do
            read -ra shape <<< "$args"
            for variant in "${order[@]}"; do
                printf "OVL memory=%s round=%d variant=%-4s shape=%s " "$memory" "$round" "$variant" "$args"
                report=$("${cmd[@]}" "$S/ovl_$variant" "${shape[@]}" 5 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V55_OVL_DONE $(date -Is)"
