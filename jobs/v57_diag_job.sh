#!/usr/bin/env bash
# v57 第一步：合并版逐内核周期与线程尾诊断（重点 K9 实际周期、k81 尾、各例 spread）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/candidate.c" -o "$S/dg_cand" -lm
sha256sum "$S/candidate.c"

shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
echo "=== DIAG per-kind cycles (HBM, merged)"
for args in "${shapes[@]}"; do
    read -ra shape <<< "$args"
    echo "DIAG memory=HBM shape=$args"
    env CONV_ROLL_DIAG=1 "${run[@]}" "$S/dg_cand" "${shape[@]}" 3 2>&1 | grep -aE "roll|best"
done
echo "=== DIAG thread spread k81 (HBM)"
env CONV_ROLL_DIAG=1 CONV_ROLL_DIAG_THR=1 "${run[@]}" "$S/dg_cand" 6390 4256 81 81 2 2>&1 | grep -aE "roll|best" | head -12
echo "=== DIAG per-kind cycles (DDR)"
for args in "${shapes[@]}"; do
    read -ra shape <<< "$args"
    echo "DIAG memory=DDR shape=$args"
    env CONV_ROLL_DIAG=1 numactl -N "$cpu_node" "$S/dg_cand" "${shape[@]}" 3 2>&1 | grep -aE "roll|best"
done
echo "V57_DIAG_DONE $(date -Is)"
