#!/usr/bin/env bash
# 滚动形态塌陷归因：THP 状态 / 内存碎片 / malloc 实际大页 / 滚动 vs 经典的 dTLB 计数
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
echo "--- THP 设置"
cat /sys/kernel/mm/transparent_hugepage/enabled /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null
echo "--- buddyinfo（node1 行，右侧为高阶大块；order9=2MB）"
grep "Node 1" /proc/buddyinfo
echo "--- meminfo 关键项"
grep -E "MemFree|AnonHugePages|HugePages_Total|CommitLimit" /proc/meminfo
echo "--- malloc 128M 实际大页占比"
gcc -O2 probe/thpprobe.c -o build/thpprobe && numactl -N 1 build/thpprobe
echo "--- perf 可用 TLB 事件"
perf list 2>/dev/null | grep -iE "tlb" | head -8
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
echo "--- k39 滚动 vs 经典：dTLB（r05 L1D_TLB_REFILL / r34 DTLB_WALK / r2d L2D_TLB_REFILL）"
for v in "X=0" "CONV_ROLL=0"; do
  echo "## env $v"
  env $v perf stat -e r05,r34,r2d,r03,r04 -- numactl -N 1 build/fbench 4096 6144 39 39 2 2>&1 | grep -E "best|r05|r34|r2d|r03|r04|seconds" | head -8
done
echo "=== DONE"; date
