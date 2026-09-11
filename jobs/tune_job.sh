#!/usr/bin/env bash
# 官方口径参数微扫：W8 / PD，k39 每档 x3
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
R="numactl -N 5 --preferred=21"
for cfg in "default" "CONV_ROLL_W8=100" "CONV_ROLL_W8=108" "CONV_ROLL_PD=2" "CONV_ROLL_PD=4" "CONV_ROLL_PD=5"; do
  echo "--- $cfg"
  for r in 1 2 3; do
    if [ "$cfg" = "default" ]; then $R build/conv2d_test 4096 6144 39 39 1 2>&1 | grep -E "PASS|FAIL" | tail -1
    else env $cfg $R build/conv2d_test 4096 6144 39 39 1 2>&1 | grep -E "PASS|FAIL" | tail -1; fi
  done
done
echo "=== DONE"; date; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
