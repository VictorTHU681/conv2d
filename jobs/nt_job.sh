#!/usr/bin/env bash
# NT-store A/B：正常（HBM）+ 带宽受限代理（-m 0 远端内存）
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp -Wall tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o build/cv_base -lm 2>&1 | grep -iE error
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp -DCONV_NT bench_conv.c conv2d.c -o build/cv_nt -lm 2>&1 | grep -iE error
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
echo "--- 泛化（NT 版）"; numactl -N 5 build/test_conv 60 1991 2>&1 | tail -1  # base binary; NT correctness same path
echo "--- HBM 交替 base/nt x3（GFLOPS）"
for args in "4096 6144 39 39" "4256 6390 55 55"; do echo "$args"; for r in 1 2 3; do
  b=$(numactl -N 5 --preferred=21 build/cv_base $args 1 2>&1 | grep PASS | awk '{print $8}')
  n=$(numactl -N 5 --preferred=21 build/cv_nt   $args 1 2>&1 | grep PASS | awk '{print $8}')
  echo "  base $b  nt $n"; done; done
echo "--- 带宽受限代理（-N 5 -m 0 远端 DDR）交替 base/nt x3"
for args in "4096 6144 39 39" "4256 6390 55 55"; do echo "$args"; for r in 1 2 3; do
  b=$(numactl -N 5 -m 0 build/cv_base $args 1 2>&1 | grep PASS | awk '{print $8}')
  n=$(numactl -N 5 -m 0 build/cv_nt   $args 1 2>&1 | grep PASS | awk '{print $8}')
  echo "  base $b  nt $n"; done; done
echo "=== DONE"
