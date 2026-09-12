#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp -Wall tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE error
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
R="numactl -N 5 --preferred=21"
echo "--- 泛化 F4"; CONV_F4=1 CONV_ROLL=1 $R build/test_conv 70 1994 2>&1 | tail -1
echo "--- 同节点 A/B：f3(默认) vs f4，k39/k55 交替 x4"
for args in "4096 6144 39 39" "4256 6390 55 55"; do echo "$args"; for r in 1 2 3 4; do
  f3=$($R build/conv2d_test $args 1 2>&1 | grep PASS | awk '{print $8}')
  f4=$(CONV_F4=1 $R build/conv2d_test $args 1 2>&1 | grep PASS | awk '{print $8}')
  echo "  f3 $f3  f4 $f4"; done; done
echo "=== DONE"
