#!/usr/bin/env bash
# 组合扫描（fbench 3 轮 best）：各例 SP × PFL2
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
fb() { echo "##### $1"; shift; numactl -N 1 build/fbench "$@" 3 2>&1 | tail -1 | sed -E "s/.*best/  best/"; }
C1="4096 6144 39 39"; C2="6144 4096 41 41"; C3="4256 6390 55 55"; C4="6390 4256 81 81"
for r in 1 2; do
fb "k39 默认(SP2)" $C1; CONV_PFL2=1 fb "k39 pfl2" $C1; CONV_SP=1 CONV_PFL2=1 fb "k39 SP1 pfl2" $C1; CONV_SP=3 CONV_PFL2=1 fb "k39 SP3 pfl2" $C1
fb "k41 默认(SP2)" $C2; CONV_PFL2=1 fb "k41 pfl2" $C2; CONV_SP=1 fb "k41 SP1" $C2; CONV_SP=1 CONV_PFL2=1 fb "k41 SP1 pfl2" $C2
fb "k55 默认(SP3)" $C3; CONV_PFL2=1 fb "k55 pfl2" $C3; CONV_SP=2 fb "k55 SP2" $C3; CONV_SP=2 CONV_PFL2=1 fb "k55 SP2 pfl2" $C3; CONV_SP=1 CONV_PFL2=1 fb "k55 SP1 pfl2" $C3
fb "k81 默认(SP1 pfl2)" $C4; CONV_SWDENSE=1 fb "k81 dense" $C4
done
echo "=== DONE"; date
