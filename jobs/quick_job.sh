#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
gcc $F -DCONV_PF_RFO tools/fbench.c conv2d.c -o build/fbench_a -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
run() { printf "  %-30s " "$1"; shift; "$@" 2>&1 | tail -1 | sed -E "s/.*best +[0-9.]+ ms +([0-9.]+) GFLOPS \| avg +[0-9.]+ ms +([0-9.]+) GFLOPS.*/best \1 avg \2/"; }
for r in 1 2; do for args in "4096 6144 39 39" "6144 4096 41 41"; do
  echo "##### $args (round $r)"
  run "v43 pstl2keep"                numactl -N 1 build/fbench_a $args 3
  run "zva postart=need(18)"         numactl -N 1 build/fbench $args 3
  run "zva postart=26"               env CONV_POSTART=26 numactl -N 1 build/fbench $args 3
  run "zva postart=36"               env CONV_POSTART=36 numactl -N 1 build/fbench $args 3
  run "zva PFST=0"                   env CONV_PFST=0 numactl -N 1 build/fbench $args 3
  run "zva PFL2=0"                   env CONV_PFL2=0 numactl -N 1 build/fbench $args 3
  run "zva 关 (ZVA=0, 无输出预取)"    env CONV_ZVA=0 numactl -N 1 build/fbench $args 3
done; done
echo "=== DONE"; date
