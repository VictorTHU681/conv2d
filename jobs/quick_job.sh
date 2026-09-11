#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc $F -DCONV_DIAG_ONLINE bench_conv.c conv2d.c -o build/conv2d_diag -lm 2>&1 | grep -iE "error|warning"
gcc $F bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
cat /sys/devices/system/cpu/cpu38/cpufreq/scaling_cur_freq
numactl -N 1 build/test_conv 100 1871 2>&1 | grep -E "FAIL|PASS"
for args in "4096 6144 39 39 1" "6390 4256 81 81 1"; do
  echo "##### diag $args"; numactl -N 1 build/conv2d_diag $args 2>&1 | grep -E "probes|burst|call 3|PASS|FAIL"
  echo "##### 无诊断 $args"; numactl -N 1 build/conv2d_test $args 2>&1 | grep -E "PASS|FAIL"
done
echo "=== DONE"; date
