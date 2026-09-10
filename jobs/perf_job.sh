#!/usr/bin/env bash
# 用 PMU 找每行 ~7 周期的固定开销：单线程 L2 驻留小规模 + 38 线程判题规模
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build; gcc $F tools/drv.c conv2d.c -o build/drv -lm 2>&1 | grep -iE "error"
[[ -x build/drv ]] || { echo "BUILD FAIL"; exit 1; }
# r11 CPU_CYCLES r08 INST_RETIRED r03 L1D_REFILL r04 L1D_ACCESS r05 L1D_TLB_REFILL r10 BR_MIS_PRED r12 BR_PRED
# r16 L2D_ACCESS r17 L2D_REFILL r24 STALL_BACKEND r23 STALL_FRONTEND r2c L2D_TLB_REFILL r34 DTLB_WALK
EV="-e r11 -e r08 -e r03 -e r04 -e r05 -e r10 -e r12 -e r16 -e r17 -e r24 -e r23 -e r2c -e r34"
pstat() { perf stat $EV -x, "$@" 2>&1 | grep -vE "^$|^#" | awk -F, '{ if (NF>3) printf "  %-8s %s\n", $3, $1; else print }'; }
export OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
echo "##### 单线程 600x1100 k39（pass 数 = 665/次 × 5 次）"
OMP_NUM_THREADS=1 CONV_PROFILE=1 pstat taskset -c 40 numactl -m 1 build/drv 600 1100 39 39 3
echo "##### 单线程 600x1100 k39 CONV_SLICE=0"
OMP_NUM_THREADS=1 CONV_SLICE=0 CONV_PROFILE=1 pstat taskset -c 40 numactl -m 1 build/drv 600 1100 39 39 3
echo "##### 单线程 600x1100 k39 CONV_PFIN=0 CONV_PFOUT=0 CONV_STORE=0"
OMP_NUM_THREADS=1 CONV_PFIN=0 CONV_PFOUT=0 CONV_STORE=0 CONV_PROFILE=1 pstat taskset -c 40 numactl -m 1 build/drv 600 1100 39 39 3
echo "##### 单线程 600x1100 k81（pass 数 = 520/次 × 5 次）"
OMP_NUM_THREADS=1 CONV_PROFILE=1 pstat taskset -c 40 numactl -m 1 build/drv 600 1100 81 81 3
echo "##### 单线程 rowbench 参照（固定行固定 R）"
(cd probe && gcc $F rowbench.c -o rowbench -lm 2>&1 | grep -iE "error"; OMP_NUM_THREADS=1 pstat taskset -c 40 ./rowbench 60000 0 39 | tail -14)
export OMP_NUM_THREADS=38
echo "##### 38 线程 case1（全进程聚合）"
CONV_PROFILE=1 pstat numactl -N 1 build/drv 4096 6144 39 39 3
echo "##### 38 线程 case4"
CONV_PROFILE=1 pstat numactl -N 1 build/drv 6390 4256 81 81 3
echo "=== DONE"; date
