#!/usr/bin/env bash
# v55 第一轮：逐内核周期诊断 + 条带长度/预取距离扫描（候选 = 远端 v54 + 按组放行 + CONV_ROLL_STEP 旋钮）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/upstream.c" -o "$S/sw_upstream" -lm
gcc "${flags[@]}" tools/fbench.c "$S/candidate.c" -o "$S/sw_candidate" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$S/candidate.c" -o "$S/sw_state" -lm
sha256sum "$S/upstream.c" "$S/candidate.c"

echo "=== STATE step4"
CONV_ROLL_STEP=4 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/sw_state" | tail -1
echo "=== STATE step32"
CONV_ROLL_STEP=32 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/sw_state" | tail -1

shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')

echo "=== DIAG per-kind cycles (HBM)"
for args in "${shapes[@]}"; do
    read -ra shape <<< "$args"
    echo "DIAG memory=HBM shape=$args"
    env CONV_ROLL_DIAG=1 "${run[@]}" "$S/sw_candidate" "${shape[@]}" 3 2>&1
done
echo "=== DIAG thread spread k39 (HBM)"
env CONV_ROLL_DIAG=1 CONV_ROLL_DIAG_THR=1 "${run[@]}" "$S/sw_candidate" 4096 6144 39 39 2 2>&1
echo "=== DIAG per-kind cycles k39/k41 (DDR)"
for args in '4096 6144 39 39' '6144 4096 41 41'; do
    read -ra shape <<< "$args"
    echo "DIAG memory=DDR shape=$args"
    env CONV_ROLL_DIAG=1 numactl -N "$cpu_node" "$S/sw_candidate" "${shape[@]}" 3 2>&1
done

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        cmd+=(--preferred="$hbm_node")
    fi
    for round in 1 2; do
        order=(upstream base step4 step16 step32 pd2 pd6)
        (( round == 2 )) && order=(pd6 pd2 step32 step16 step4 base upstream)
        for args in "${shapes[@]}"; do
            read -ra shape <<< "$args"
            for variant in "${order[@]}"; do
                case "$variant" in
                    upstream) exe="$S/sw_upstream"; mode=() ;;
                    base)     exe="$S/sw_candidate"; mode=() ;;
                    step4)    exe="$S/sw_candidate"; mode=(CONV_ROLL_STEP=4) ;;
                    step16)   exe="$S/sw_candidate"; mode=(CONV_ROLL_STEP=16) ;;
                    step32)   exe="$S/sw_candidate"; mode=(CONV_ROLL_STEP=32) ;;
                    pd2)      exe="$S/sw_candidate"; mode=(CONV_ROLL_PD=2) ;;
                    pd6)      exe="$S/sw_candidate"; mode=(CONV_ROLL_PD=6) ;;
                esac
                printf "SWEEP memory=%s round=%d variant=%-8s shape=%s " "$memory" "$round" "$variant" "$args"
                report=$(env "${mode[@]}" "${cmd[@]}" "$exe" "${shape[@]}" 5 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V55_DIAG_SWEEP_DONE $(date -Is)"
