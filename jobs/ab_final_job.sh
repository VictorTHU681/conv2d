#!/usr/bin/env bash
# 同节点 roll vs classic A/B（交替，抵消漂移），四例各 x4
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
R="numactl -N 5 --preferred=21"
for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
  echo "--- $args  (roll / classic 交替 x4)"
  for r in 1 2 3 4; do
    ro=$($R build/conv2d_test $args 1 2>&1 | grep -oE "[0-9]+\.[0-9]+ +0.00e" | head -1)
    cl=$(CONV_ROLL=0 $R build/conv2d_test $args 1 2>&1 | grep -oE "[0-9]+\.[0-9]+ +0.00e" | head -1)
    echo "  roll $($R build/conv2d_test $args 1 2>&1 | grep -E 'PASS' | awk '{print $7}')  classic $(CONV_ROLL=0 $R build/conv2d_test $args 1 2>&1 | grep -E 'PASS' | awk '{print $7}')"
  done
done
echo "=== DONE"; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
