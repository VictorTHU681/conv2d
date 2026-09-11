#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
R="numactl -N 5 --preferred=21"
CONV_ROLL=1 $R perf record -e cycles:u -F 6000 -o /tmp/perf_roll.data build/fbench_g 4096 6144 39 39 4 >/dev/null 2>&1
echo "--- roll_worker 注解（≥0.3%，含上下文）"
perf annotate -i /tmp/perf_roll.data --stdio -s roll_worker 2>/dev/null | awk '$1+0 > 0.3 {print NR": "$0}' | head -50
echo "--- roll_worker 指令类型汇总"
perf annotate -i /tmp/perf_roll.data --stdio -s roll_worker 2>/dev/null | awk '$1+0>0 {sum[$3]+=$1} END {for (k in sum) printf "%8.2f  %s\n", sum[k], k}' | sort -rn | head -18
echo "=== DONE"
