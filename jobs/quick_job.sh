#!/usr/bin/env bash
# 验证 + 干扰复现（kernel 缓存去屏障 + 剔核 + futex 停车）+ 无干扰 A/B
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; cat /sys/devices/system/cpu/cpu38/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc $F -DCONV_DIAG_ONLINE bench_conv.c conv2d.c -o build/conv2d_diag -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c build/conv2d_v43a.c -o build/fbench_v43 -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
numactl -N 1 build/test_conv 120 1901 2>&1 | grep -E "FAIL|PASS"
CONV_BR=0 numactl -N 1 build/test_conv 30 1902 2>&1 | grep -E "FAIL|PASS"
OMP_NUM_THREADS=5 numactl -N 1 build/test_conv 30 1903 2>&1 | grep -E "FAIL|PASS"
echo "--- 基线（诊断）"; numactl -N 1 build/conv2d_diag 4096 6144 39 39 1 2>&1 | grep -E "cpu probe|call 3|PASS"
echo "--- 干扰 (CPU 45,60) ×3 k39 + k81"
taskset -c 45 sh -c 'while :; do :; done' & P1=$!; taskset -c 60 sh -c 'while :; do :; done' & P2=$!; sleep 1
for i in 1 2 3; do CONV_DIAG_THR=1 numactl -N 1 build/conv2d_diag 4096 6144 39 39 1 2>&1 | grep -E "cpu probe|call 3|PASS|thr "; done
numactl -N 1 build/conv2d_diag 6390 4256 81 81 1 2>&1 | grep -E "cpu probe|call 3|PASS"
echo "--- 干扰下 探测关"; CONV_CPUPROBE=0 numactl -N 1 build/conv2d_diag 4096 6144 39 39 1 2>&1 | grep -E "call 3|PASS"
kill $P1 $P2; wait 2>/dev/null
echo "--- 无干扰 A/B v43 vs cur（含 --preferred=17）"
run() { printf "  %-22s %-16s " "$1" "$2"; shift 2; "$@" 2>&1 | tail -1 | sed -E "s/.*best +[0-9.]+ ms +([0-9.]+) GFLOPS \| avg +[0-9.]+ ms +([0-9.]+) GFLOPS.*/best \1 avg \2/"; }
for r in 1 2 3; do for args in "4096 6144 39 39" "6144 4096 41 41"; do
  run v43 "$args" numactl -N 1 build/fbench_v43 $args 3
  run cur "$args" numactl -N 1 build/fbench $args 3
  run "cur HBM" "$args" numactl -N 1 --preferred=17 build/fbench $args 3
  run "v43 HBM" "$args" numactl -N 1 --preferred=17 build/fbench_v43 $args 3
done; done
echo "=== DONE"; date
