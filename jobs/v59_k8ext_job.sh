#!/usr/bin/env bash
# v59 候选：k8 滑窗 EXT（k41 主攻）。base = v58（newcand.c 槽），cand = k8ext.c。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/newcand.c" -o "$S/e_base" -lm
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/e_cand" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$S/k8ext.c" -o "$S/e_state" -lm
sha256sum "$S/newcand.c" "$S/k8ext.c"

echo "=== STATE"
TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/e_state" | tail -1
echo "=== STATE packser3 step4"
CONV_PACKSER=3 CONV_ROLL_STEP=4 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/e_state" | tail -1

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
                printf "E memory=%s round=%d variant=%-5s shape=%s " "$memory" "$round" "$v" "$args"
                report=$("${cmd[@]}" "$S/e_$v" "${shape[@]}" 5 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V59_K8EXT_DONE $(date -Is)"
