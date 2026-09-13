#!/usr/bin/env bash
# v57 候选2：kf 表同形共享（k81 两个 pairf4 组）+ K9 权重扫描。
# base = v57 门控版（v55.c 槽），cand = kf 共享版（newcand.c）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/v55.c" -o "$S/kf_base" -lm
gcc "${flags[@]}" tools/fbench.c "$S/newcand.c" -o "$S/kf_cand" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$S/newcand.c" -o "$S/kf_state" -lm
sha256sum "$S/v55.c" "$S/newcand.c"

echo "=== STATE"
TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/kf_state" | tail -1
echo "=== STATE packser3"
CONV_PACKSER=3 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/kf_state" | tail -1

shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; cmd+=(--preferred="$hbm_node"); fi
    for round in 1 2 3; do
        order=(base cand w130 w135 w150)
        (( round == 2 )) && order=(w150 w135 w130 cand base)
        (( round == 3 )) && order=(cand w130 base w150 w135)
        for args in "${shapes[@]}"; do
            read -ra shape <<< "$args"
            for v in "${order[@]}"; do
                case "$v" in
                    base) exe="$S/kf_base"; mode=() ;;
                    cand) exe="$S/kf_cand"; mode=() ;;
                    w130) exe="$S/kf_cand"; mode=(CONV_ROLL_W9=130) ;;
                    w135) exe="$S/kf_cand"; mode=(CONV_ROLL_W9=135) ;;
                    w150) exe="$S/kf_cand"; mode=(CONV_ROLL_W9=150) ;;
                esac
                printf "KF memory=%s round=%d variant=%-5s shape=%s " "$memory" "$round" "$v" "$args"
                report=$(env "${mode[@]}" "${cmd[@]}" "$exe" "${shape[@]}" 5 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V57_KF_DONE $(date -Is)"
