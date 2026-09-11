#!/usr/bin/env bash
# 验证 + A/B：v43 vs cur（sweep 收尾少分支 + asm 初值 + 免除法解码）+ rowprof
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; cat /sys/devices/system/cpu/cpu38/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc $F tools/fbench.c build/conv2d_v43a.c -o build/fbench_v43 -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
gcc $F -DCONV_DIAG_ONLINE -DCONV_ROWPROF bench_conv.c conv2d.c -o build/conv2d_rowprof -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
numactl -N 1 build/test_conv 200 1861 2>&1 | grep -E "FAIL|PASS"
CONV_SWDENSE=1 numactl -N 1 build/test_conv 40 1862 2>&1 | grep -E "FAIL|PASS"
CONV_SWDENSE=0 numactl -N 1 build/test_conv 40 1863 2>&1 | grep -E "FAIL|PASS"
CONV_STORE=0 numactl -N 1 build/test_conv 40 1864 2>&1 | grep -E "FAIL|PASS"
CONV_SP=1 numactl -N 1 build/test_conv 40 1865 2>&1 | grep -E "FAIL|PASS"
OMP_NUM_THREADS=5 numactl -N 1 build/test_conv 40 1866 2>&1 | grep -E "FAIL|PASS"
OMP_NUM_THREADS=1 numactl -N 1 build/test_conv 12 1867 2>&1 | grep -E "FAIL|PASS"
CONV_BR=0 numactl -N 1 build/test_conv 30 1868 2>&1 | grep -E "FAIL|PASS"
echo "--- rowprof k39"
numactl -N 1 build/conv2d_rowprof 4096 6144 39 39 1 2>&1 | grep -E "rowprof|^ *[0-9]+:"
run() { printf "  %-8s %-16s " "$1" "$2"; shift 2; "$@" 2>&1 | tail -1 | sed -E "s/.*best +[0-9.]+ ms +([0-9.]+) GFLOPS \| avg +[0-9.]+ ms +([0-9.]+) GFLOPS.*/best \1 avg \2/"; }
for r in 1 2 3; do for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
  run v43 "$args" numactl -N 1 build/fbench_v43 $args 3
  run cur "$args" numactl -N 1 build/fbench $args 3
done; done
echo "=== DONE"; date
