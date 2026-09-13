#!/usr/bin/env bash
# v61 验证：TBc 键控缓存删除（classic 路径）+ 依赖重试修复的整包正确性与快速性能对照。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/v_cand" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$S/k8ext.c" -o "$S/v_state" -lm
gcc -O3 -fopenmp tools/test_conv.c "$S/k8ext.c" -o "$S/v_general" -lm
sha256sum "$S/k8ext.c"

echo "=== STATE rolling"
TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/v_state" | tail -1
echo "=== CLASSIC bitwise (CONV_ROLL=0)"
env CONV_ROLL=0 TEST_BITWISE=1 TEST_SIGNED=1 TEST_REUSE_HEIGHT=1 "${run[@]}" "$S/v_general" 80 55901 | tail -3
echo "=== DEFAULT bitwise"
env TEST_BITWISE=1 TEST_SIGNED=1 TEST_REUSE_HEIGHT=1 "${run[@]}" "$S/v_general" 80 55902 | tail -3
echo "=== FALLBACK bitwise (CONV_NO_SME=1)"
env CONV_NO_SME=1 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/v_general" 40 55903 | tail -3

echo "=== QUICK officials"
for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    report=$("${run[@]}" "$S/v_cand" "${shape[@]}" 5 2>&1)
    printf '%s\n' "$report" | tail -1
    [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
done
echo "V61_VAL_DONE $(date -Is)"
