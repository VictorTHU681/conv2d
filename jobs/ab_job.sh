#!/usr/bin/env bash
# 验证 + 同节点 A/B：v43 vs cur（哑 sweep + 无 cbz 预取游标） vs cur SWDUMMY=0 vs cur + POSTART=Ymain（输出预取从 pass 头开始）
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc $F tools/fbench.c build/conv2d_v43a.c -o build/fbench_v43 -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
numactl -N 1 build/test_conv 150 1821 2>&1 | grep -E "FAIL|PASS"
CONV_SWDENSE=1 numactl -N 1 build/test_conv 40 1822 2>&1 | grep -E "FAIL|PASS"
CONV_SWDENSE=0 numactl -N 1 build/test_conv 40 1823 2>&1 | grep -E "FAIL|PASS"
CONV_STORE=0 numactl -N 1 build/test_conv 40 1824 2>&1 | grep -E "FAIL|PASS"
CONV_SP=1 numactl -N 1 build/test_conv 40 1825 2>&1 | grep -E "FAIL|PASS"
OMP_NUM_THREADS=5 numactl -N 1 build/test_conv 40 1826 2>&1 | grep -E "FAIL|PASS"
OMP_NUM_THREADS=1 numactl -N 1 build/test_conv 12 1827 2>&1 | grep -E "FAIL|PASS"
CONV_BR=0 numactl -N 1 build/test_conv 30 1828 2>&1 | grep -E "FAIL|PASS"
CONV_PFIN=0 CONV_PFOUT=0 numactl -N 1 build/test_conv 30 1829 2>&1 | grep -E "FAIL|PASS"
run() { printf "  %-30s " "$1"; shift; "$@" 2>&1 | tail -1 | sed -E "s/.*best +[0-9.]+ ms +([0-9.]+) GFLOPS \| avg +[0-9.]+ ms +([0-9.]+) GFLOPS.*/best \1 avg \2/"; }
declare -A YM=( ["4096 6144 39 39"]=38 ["6144 4096 41 41"]=40 ["4256 6390 55 55"]=54 ["6390 4256 81 81"]=80 )
for r in 1 2; do for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
  echo "##### $args (round $r)"
  run "v43"                          numactl -N 1 build/fbench_v43 $args 3
  run "cur（哑 sweep + 无 cbz 游标）"   numactl -N 1 build/fbench $args 3
  run "cur SWDUMMY=0"                env CONV_SWDUMMY=0 numactl -N 1 build/fbench $args 3
  run "cur POSTART=Ymain"            env CONV_POSTART=${YM[$args]} numactl -N 1 build/fbench $args 3
done; done
echo "=== DONE"; date
