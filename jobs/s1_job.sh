#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp -Wall tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE error
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
R="numactl -N 5 --preferred=21"
echo "--- 泛化（S1 默认开）"; $R build/test_conv 90 1998 2>&1 | tail -1; $R build/test_conv 90 1999 2>&1 | tail -1
echo "--- k55 同节点 A/B：S1=1(默认,single16f1) vs S1=0(旧)，x5"
for r in 1 2 3 4 5; do
  s1=$($R build/conv2d_test 4256 6390 55 55 1 2>&1 | grep PASS | awk '{print $8}')
  s0=$(CONV_S1=0 $R build/conv2d_test 4256 6390 55 55 1 2>&1 | grep PASS | awk '{print $8}')
  echo "  S1 $s1  S0 $s0"; done
echo "--- k39/k41/k81 默认确认 x2（无扰动）"
for args in "4096 6144 39 39" "6144 4096 41 41" "6390 4256 81 81"; do for r in 1 2; do $R build/conv2d_test $args 1 2>&1 | grep PASS | awk '{print $1" "$3" "$8}'; done; done
echo "=== DONE"
