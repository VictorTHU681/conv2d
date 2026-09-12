#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp -Wall tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE error
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
R="numactl -N 5 --preferred=21"
echo "--- 泛化（默认）"; $R build/test_conv 80 1996 2>&1 | tail -1
echo "--- k41 同节点 A/B：默认(nf=4) vs nf=1 vs nf=0，x4"
for r in 1 2 3 4; do
  d=$($R build/conv2d_test 6144 4096 41 41 1 2>&1 | grep PASS | awk '{print $8}')
  n1=$(CONV_NF=1 $R build/conv2d_test 6144 4096 41 41 1 2>&1 | grep PASS | awk '{print $8}')
  n0=$(CONV_NF=0 $R build/conv2d_test 6144 4096 41 41 1 2>&1 | grep PASS | awk '{print $8}')
  echo "  nf4 $d  nf1 $n1  nf0 $n0"; done
echo "--- k81 同节点 A/B：默认(nf=1) vs nf=4 vs nf=0，x4"
for r in 1 2 3 4; do
  d=$($R build/conv2d_test 6390 4256 81 81 1 2>&1 | grep PASS | awk '{print $8}')
  n4=$(CONV_NF=4 $R build/conv2d_test 6390 4256 81 81 1 2>&1 | grep PASS | awk '{print $8}')
  echo "  def $d  nf4 $n4"; done
echo "--- k39/k55 默认确认 x2"
for args in "4096 6144 39 39" "4256 6390 55 55"; do for r in 1 2; do $R build/conv2d_test $args 1 2>&1 | grep PASS | awk '{print $1" "$3" "$8}'; done; done
echo "=== DONE"
