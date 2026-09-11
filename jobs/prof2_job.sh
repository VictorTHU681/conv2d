#!/usr/bin/env bash
# 深度 profile：perf record 到指令级（滚动 k39），+ 派发/汇合计时
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp -g -fno-omit-frame-pointer tools/fbench.c conv2d.c -o build/fbench_g -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
R="numactl -N 5 --preferred=21"
echo "--- 派发/汇合计时（wall vs thr max）"
CONV_ROLL=1 CONV_ROLL_DIAG=1 $R build/fbench_g 4096 6144 39 39 3 2>&1 | grep -E "best|\[roll\]"
echo "--- perf record k39 滚动"
CONV_ROLL=1 $R perf record -e cycles:u -F 4000 -o /tmp/perf_roll.data build/fbench_g 4096 6144 39 39 3 >/dev/null 2>&1
perf report -i /tmp/perf_roll.data --stdio 2>/dev/null | head -15
echo "--- annotate k16pair 热点（周期占比 > 0.8%）"
perf annotate -i /tmp/perf_roll.data --stdio -s k16pair 2>/dev/null | awk '$1+0 > 0.8' | head -40
echo "--- annotate roll_worker/k8"
perf annotate -i /tmp/perf_roll.data --stdio -s k8 2>/dev/null | awk '$1+0 > 1.5' | head -15
echo "=== DONE"; date
