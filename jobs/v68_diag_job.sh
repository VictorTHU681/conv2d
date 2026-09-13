#!/usr/bin/env bash
# v68 侦察：v66/v67 形态下的全套新鲜诊断（逐内核周期、claim 时间线、逐线程分布）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/s_diag" -lm
sha256sum "$S/k8ext.c"

for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    echo "DIAG2 shape=$args"
    env CONV_ROLL_DIAG=2 CONV_ROLL_DIAG_THR=1 "${run[@]}" "$S/s_diag" "${shape[@]}" 3 2>&1 | grep -aE "roll|tl\]|^  p|best|:[0-9]" | tail -50
done
echo "V68_DIAG_DONE $(date -Is)"
