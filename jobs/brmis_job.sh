#!/usr/bin/env bash
# 分支预测失败归因：r10 计数（默认/无 sweep/BR=0）+ 按 r10 采样到指令
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp -g"; mkdir -p build prof
gcc $F tools/drv.c conv2d.c -o build/drv_g -lm 2>&1 | grep -iE "error"
gcc $F -DCONV_NOHALF tools/drv.c conv2d.c -o build/drv_nohalf -lm 2>&1 | grep -iE "error"
export OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE OMP_NUM_THREADS=1
pst() { perf stat "$@" 2>&1 | grep -E "^ +[0-9,<]" | awk '{ n=$1; gsub(",","",n); printf "  %-8s %14s", $2, n } END { print "" }'; }
echo "--- 1 线程 全尺寸 k39（2 次调用，24360 pass/次）：r11 cycles r08 inst r10 br_mis r12 br_pred r21 br_retired r22 br_mis_retired"
echo "默认:";   pst -e r11:u -e r08:u -e r10:u -e r12:u -e r21:u -e r22:u numactl -N 1 taskset -c 40 build/drv_g 4096 6144 39 39 2
echo "无sweep:"; pst -e r11:u -e r08:u -e r10:u -e r12:u -e r21:u -e r22:u numactl -N 1 taskset -c 40 build/drv_nohalf 4096 6144 39 39 2
echo "BR=0:";   CONV_BR=0 pst -e r11:u -e r08:u -e r10:u -e r12:u -e r21:u -e r22:u numactl -N 1 taskset -c 40 build/drv_g 4096 6144 39 39 2
echo "a+b L1:"; CONV_DIAG_L1=2 pst -e r11:u -e r08:u -e r10:u -e r12:u -e r21:u -e r22:u numactl -N 1 taskset -c 40 build/drv_g 4096 6144 39 39 2
echo "k81 默认:"; pst -e r11:u -e r08:u -e r10:u -e r12:u -e r21:u -e r22:u numactl -N 1 taskset -c 40 build/drv_g 6390 4256 81 81 1
echo "--- 按 r22（BR_MIS_PRED_RETIRED）采样归因（38 线程 k39）"
export OMP_NUM_THREADS=38
perf record -e r22:u -c 20 -o prof/k39_brmis.data numactl -N 1 build/drv_g 4096 6144 39 39 5 2>&1 | grep samples
echo "## 符号级"; perf report -i prof/k39_brmis.data --stdio --sort sym 2>/dev/null | grep -vE "^#|^$" | head -6
perf annotate -i prof/k39_brmis.data --stdio --no-source pass_steps 2>/dev/null > prof/k39_brmis.annot.txt
echo "## pass_steps 最热 30 条（采样落点通常是分支之后的指令）"; awk '/^ +[0-9]+\.[0-9]+ +:/ { print }' prof/k39_brmis.annot.txt | sort -k1 -nr | head -30
echo "## conv_worker 最热 10 条"; perf annotate -i prof/k39_brmis.data --stdio --no-source conv_worker 2>/dev/null | awk '/^ +[0-9]+\.[0-9]+ +:/ { print }' | sort -k1 -nr | head -10
echo "--- 按 r10（BR_MIS_PRED，推测）采样"
perf record -e r10:u -c 20 -o prof/k39_brmis10.data numactl -N 1 build/drv_g 4096 6144 39 39 5 2>&1 | grep samples
perf annotate -i prof/k39_brmis10.data --stdio --no-source pass_steps 2>/dev/null > prof/k39_brmis10.annot.txt
echo "## pass_steps 最热 20 条"; awk '/^ +[0-9]+\.[0-9]+ +:/ { print }' prof/k39_brmis10.annot.txt | sort -k1 -nr | head -20
echo "=== DONE"; date
