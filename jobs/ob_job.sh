#!/usr/bin/env bash
# 官方 bench 口径的 A/B：默认（roll k39）/ 强制 roll（看 k55/k41）/ 强制经典
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
R="numactl -N 5 --preferred=21"
echo "--- 默认（roll k39，其余经典）x3"
for r in 1 2 3; do for args in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do $R build/conv2d_test $args 2>&1 | grep -E "PASS|FAIL" | tail -1; done; done
echo "--- 强制经典 k39 x3"
for r in 1 2 3; do CONV_ROLL=0 $R build/conv2d_test 4096 6144 39 39 1 2>&1 | grep -E "PASS|FAIL" | tail -1; done
echo "=== DONE"; date
