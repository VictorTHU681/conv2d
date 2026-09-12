#!/usr/bin/env bash
# pair+fmla 验证：泛化（强制滚动）+ k41/k81 官方口径 A/B
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp -Wall tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE "error"
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
R="numactl -N 5 --preferred=21"
echo "--- 泛化 强制滚动（含 KH%16==9/1 形状）x2 种子"
CONV_ROLL=1 $R build/test_conv 80 1931 2>&1 | grep -E "FAIL|PASS"
CONV_ROLL=1 $R build/test_conv 80 1932 2>&1 | grep -E "FAIL|PASS"
echo "--- fbench 滚动 k41/k81（诊断）"
CONV_ROLL=1 CONV_ROLL_DIAG=1 $R build/fbench 6144 4096 41 41 3 2>&1 | grep -E "best|\[roll\]" | tail -2
CONV_ROLL=1 CONV_ROLL_DIAG=1 $R build/fbench 6390 4256 81 81 2 2>&1 | grep -E "best|\[roll\]" | tail -2
echo "--- 官方 k41：滚动 x3 vs 经典 x3"
for r in 1 2 3; do CONV_ROLL=1 $R build/conv2d_test 6144 4096 41 41 1 2>&1 | grep -E "PASS|FAIL" | tail -1; done
for r in 1 2 3; do CONV_ROLL=0 $R build/conv2d_test 6144 4096 41 41 1 2>&1 | grep -E "PASS|FAIL" | tail -1; done
echo "--- 官方 k39 默认 x2（确认无扰动）"
for r in 1 2; do $R build/conv2d_test 4096 6144 39 39 1 2>&1 | grep -E "PASS|FAIL" | tail -1; done
echo "=== DONE"; date
