#!/usr/bin/env bash
# 深度剖析：perf record/annotate（指令级热点）、符号级分布、单线程 PMU 对照、每线程时间线
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp -g"; mkdir -p build prof
gcc $F tools/drv.c conv2d.c -o build/drv_g -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
C1="4096 6144 39 39"; C4="6390 4256 81 81"
echo "--- perf record 可用性"
perf record -e cycles:u -F 4000 -o prof/k39.data numactl -N 1 build/drv_g $C1 5 2>&1 | tail -2
perf record -e cycles:u -F 4000 -o prof/k81.data numactl -N 1 build/drv_g $C4 3 2>&1 | tail -2
for k in k39 k81; do
  echo "##### $k 符号级分布（cycles:u）"
  perf report -i prof/$k.data --stdio --sort sym 2>/dev/null | grep -vE "^#|^$" | head -14
  echo "##### $k pass_steps 指令级：按助记符聚合（样本%）"
  perf annotate -i prof/$k.data --stdio --no-source pass_steps 2>/dev/null > prof/$k.annot.txt
  awk '/^ +[0-9]+\.[0-9]+ +:/ { pct=$1; for(i=3;i<=NF;i++) if ($i !~ /^[0-9a-f]+:$/ && $i !~ /^:$/) { m=$i; break } sum[m]+=pct; n[m]++ } END { for (m in sum) printf "  %-10s %7.2f%%  (%d 条)\n", m, sum[m], n[m] }' prof/$k.annot.txt | sort -k2 -nr | head -20
  echo "##### $k pass_steps 最热的 25 条指令"
  awk '/^ +[0-9]+\.[0-9]+ +:/ { print }' prof/$k.annot.txt | sort -k1 -nr | head -25
done
echo "##### k39 conv_worker（C 段）热点前 15"
perf annotate -i prof/k39.data --stdio --no-source conv_worker 2>/dev/null | awk '/^ +[0-9]+\.[0-9]+ +:/ { print }' | sort -k1 -nr | head -15
echo "--- 单线程 L2 驻留对照（PMU）：r11 cycles r08 inst r23 stall_frontend r24 stall_backend r03 L1 refill r10 br_mis r0d? (BR_IMMED) r1b INST_SPEC"
EV="-e r11 -e r08 -e r23 -e r24 -e r03 -e r10 -e r1b"
pstat() { perf stat $EV -x, "$@" 2>&1 | grep -E "^[0-9]" | awk -F, '{printf "  %-8s %s\n", $3, $1}'; }
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp tools/drv.c conv2d.c -o build/drv -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=1
for cfg in "BR=1 默认:" "BR=0:CONV_BR=0" "BR=1 无切片无预取:CONV_SLICE=0 CONV_PFIN=0 CONV_PFOUT=0" "BR=0 无切片无预取无回写:CONV_BR=0 CONV_SLICE=0 CONV_PFIN=0 CONV_PFOUT=0 CONV_STORE=0"; do
  name=${cfg%%:*}; envs=${cfg#*:}
  echo "##### 1 线程 600x1100 k39 [$name]"; env $envs CONV_PROFILE=1 numactl -N 1 taskset -c 40 build/drv 600 1100 39 39 3 2>&1 | grep -E "GFLOPS|conv prof" | tail -2 | sed -E "s/\| pre.*enter max/| enter max/"
  env $envs perf stat $EV -x, numactl -N 1 taskset -c 40 build/drv 600 1100 39 39 3 2>&1 | grep -E "^[0-9]" | awk -F, '{printf "  %-8s %s\n", $3, $1}'
done
echo "--- 每线程时间线 k39（最后一次调用；按 total 排序）"
export OMP_NUM_THREADS=38
CONV_PROFILE=2 numactl -N 1 build/drv $C1 1 2>&1 | grep -E "^  t|conv prof" | tail -39 | sort -k6 -n | awk 'NR<=3 || NR>=36 {print} NR==4 {print "  ..."}'
echo "=== DONE"; date
