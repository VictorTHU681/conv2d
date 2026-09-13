#!/usr/bin/env bash
# v65 正式版：非官方用例正确性扫描（逐位哈希对比 naive 参考）。
# 覆盖：sweep/通用路径（KH<16 或 KW<3 或超界）、roll 全余数类（KH 16..256）、矩形核、
# 宽度门控边界（outW 63..320）、outH=1 等行数边界、极小 KW（K4E/K5/k8 尾部公式）、
# 线程数 1/7/38、rem7 的 NF=3 覆盖（nf3 包逻辑）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/s_edge" -lm
sha256sum "$S/k8ext.c"
RC=refcache_edge; mkdir -p "$RC"

pass=0; fail=0
run_case() {  # env... H W KH KW
    local envs=() ; while [[ "$1" == *=* ]]; do envs+=("$1"); shift; done
    local H=$1 W=$2 KH=$3 KW=$4
    local out
    out=$(env "${envs[@]}" "${run[@]}" "$S/s_edge" "$H" "$W" "$KH" "$KW" 1 "$RC" 2>&1 | tail -1)
    if [[ "$out" == *PASS* && "$out" != *FAIL* ]]; then
        pass=$((pass+1))
    else
        fail=$((fail+1)); echo "EDGE_FAIL ${envs[*]} $H $W $KH $KW :: $out"
    fi
}

# A. sweep/通用路径（roll 范围之外）
for kh in 1 2 3 5 8 15; do run_case 300 300 $kh $kh; done
run_case 300 300 15 2;  run_case 300 300 8 1;  run_case 300 300 1 15
run_case 300 700 12 300; run_case 700 300 257 3
run_case 700 500 257 257; run_case 300 900 16 401; run_case 300 900 5 401

# B. roll 全余数类（KH 16..256 的代表集，方核，W 保证 outW≥256+KW）
for kh in 16 17 23 25 31 32 33 39 41 47 48 49 55 63 64 65 71 73 80 81 89 96 97 105 113 127 128 129 145 161 177 193 209 225 241 256; do
    run_case 400 700 $kh $kh
done

# C. 矩形核（KH≠KW 两个方向、奇偶 KW、极小/极大 KW）
for kw in 3 4 5 6 7 17 80 399; do run_case 400 900 41 $kw; done
for kw in 3 4 9 33 81 175; do run_case 400 900 81 $kw; done
for kw in 3 4 16 39 55; do run_case 400 900 55 $kw; done
for kh in 16 17 33 49 65 97 129; do run_case 400 900 $kh 7; done
run_case 300 900 39 398; run_case 300 900 17 399; run_case 900 400 255 4

# D. 宽度门控边界（outW 63..321：W = outW+KW-1；覆盖 K9(128)/K5(192)/K4(256) 门槛两侧）
for ow in 63 64 65 127 128 129 191 192 193 255 256 257 320; do
    for kh in 39 41 55 81; do
        run_case 400 $((ow + kh - 1)) $kh $kh
    done
done

# E. 行数边界（outH=1/2/10/64/201）
for kh in 16 39 41 55 81 129; do
    for dh in 0 1 9 63 200; do
        run_case $((kh + dh)) 700 $kh $kh
    done
done
run_case 43 43 41 41   # outW=3、outH=3（双维极小，roll 拒绝→sweep）
run_case 41 700 41 41  # outH=1
run_case 200 43 41 43  # outW=1

# F. 中等规模抽样（roll 主路径的较大 outH/outW 组合）
run_case 900 900 81 81
run_case 800 1200 55 55
run_case 1200 800 41 41
run_case 1000 1000 39 39
run_case 700 1500 73 73
run_case 1500 700 97 97

# G. rem7 的 NF=3 覆盖（nf3 包默认逻辑）+ NF=0 显式
for kh in 39 55 71 103; do
    run_case CONV_NF=3 400 900 $kh $kh
    run_case CONV_NF=0 400 900 $kh $kh
done

# H. 线程数变化（小尺寸避免串行参考过慢；覆盖 nth>npieces、串行、奇数线程）
for nt in 1 7 38; do
    run_case OMP_NUM_THREADS=$nt 200 500 41 41
    run_case OMP_NUM_THREADS=$nt 100 400 81 81
    run_case OMP_NUM_THREADS=$nt 300 400 55 17
done

# I. 打包模式覆盖（旋钮 CONV_PACKSER：0 全并行、1 按组重叠、2 完整串行基线）
for ps in 0 1 2; do
    run_case CONV_PACKSER=$ps 400 700 41 41
    run_case CONV_PACKSER=$ps 400 700 81 81
done

echo "EDGE_SUMMARY pass=$pass fail=$fail"
echo "V65_EDGE_DONE $(date -Is)"
