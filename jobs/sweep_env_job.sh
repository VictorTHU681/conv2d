#!/usr/bin/env bash
# 环境变量小扫描（fbench 3 轮取 best）：k81 SP=2、各例密度/回写/预取层级；每线程分相看不均衡
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
gcc $F tools/drv.c conv2d.c -o build/drv -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
fb() { echo "##### $1"; shift; numactl -N 1 build/fbench "$@" 3 2>&1 | tail -1 | sed -E "s/.*best/  best/"; }
C1="4096 6144 39 39"; C2="6144 4096 41 41"; C3="4256 6390 55 55"; C4="6390 4256 81 81"
fb "k81 默认(SP=1 sparse store0 pfl2)" $C4
CONV_SP=2 fb "k81 SP=2" $C4
CONV_SP=2 CONV_SWDENSE=1 fb "k81 SP=2 dense" $C4
CONV_PFL2=0 fb "k81 pfl2=0" $C4
CONV_STORE=1 fb "k81 store=1" $C4
fb "k55 默认(SP=3 sparse)" $C3
CONV_SP=2 fb "k55 SP=2" $C3
CONV_SWDENSE=1 fb "k55 dense" $C3
CONV_PFL2=1 fb "k55 pfl2=1" $C3
CONV_STORE=0 fb "k55 store=0" $C3
fb "k39 默认(SP=2 dense)" $C1
CONV_SP=1 fb "k39 SP=1" $C1
CONV_PFL2=1 fb "k39 pfl2=1" $C1
CONV_STORE=0 fb "k39 store=0" $C1
fb "k41 默认" $C2
CONV_SP=1 fb "k41 SP=1" $C2
CONV_PFL2=1 fb "k41 pfl2=1" $C2
echo "--- 每线程分相 k39 / k81（最后一次调用）"
for c in "$C1" "$C4"; do echo "##### $c"; CONV_PROFILE=2 numactl -N 1 build/drv $c 1 2>&1 | grep -E "^  t|conv prof" | tail -39 | sort -k6 -n | sed -n '1,3p;36,39p'; done
echo "=== DONE"; date
