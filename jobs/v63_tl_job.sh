#!/usr/bin/env bash
# v63 侦察：k81/k55 claim 时间线（CONV_ROLL_DIAG=2），看尾部是否依赖链串行。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/s_tl" -lm
sha256sum "$S/k8ext.c"

for args in '6390 4256 81 81' '4256 6390 55 55'; do
    read -ra shape <<< "$args"
    echo "TL shape=$args"
    env CONV_ROLL_DIAG=2 "${run[@]}" "$S/s_tl" "${shape[@]}" 2 2>&1 | grep -aE "roll|tl\]|  p|best" | tail -75
done
echo "V63_TL_DONE $(date -Is)"
