#!/usr/bin/env bash
# 内存敏感性：本地内存 vs 远端内存（-m 0，延迟更高/带宽更低）；BR 开/关；线程数减半的每线程吞吐；预取开关
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
run() { printf "  %-34s " "$1"; shift; "$@" 2>&1 | tail -1 | sed -E "s/.*best +([0-9.]+) ms +([0-9.]+) GFLOPS \| avg +[0-9.]+ ms +([0-9.]+) GFLOPS.*/best \2 avg \3  (\1 ms)/"; }
for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
  echo "##### $args"
  run "本地内存 (-N 1)"            numactl -N 1 build/fbench $args 3
  run "远端内存 (-N 1 -m 0)"       numactl -N 1 -m 0 build/fbench $args 3
  run "本地 BR=0"                  env CONV_BR=0 numactl -N 1 build/fbench $args 3
  run "远端 BR=0"                  env CONV_BR=0 numactl -N 1 -m 0 build/fbench $args 3
  run "本地 PFOUT=0"               env CONV_PFOUT=0 numactl -N 1 build/fbench $args 3
  run "本地 PFIN=0"                env CONV_PFIN=0 numactl -N 1 build/fbench $args 3
  run "本地 19 线程"               env OMP_NUM_THREADS=19 numactl -N 1 build/fbench $args 2
  run "远端 19 线程"               env OMP_NUM_THREADS=19 numactl -N 1 -m 0 build/fbench $args 2
done
echo "=== DONE"; date
