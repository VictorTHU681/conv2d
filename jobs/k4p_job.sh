#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp -g tools/fbench.c conv2d.c -o build/fbench_g -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
R="numactl -N 5 --preferred=21"
CONV_ROLL=1 $R perf record -e cycles:u -F 6000 -o /tmp/pk.data build/fbench_g 4096 6144 39 39 4 >/dev/null 2>&1
echo "--- k4 注解（≥0.5%）"
perf annotate -i /tmp/pk.data --stdio -s k4 2>/dev/null | awk '$1+0 > 0.5' | head -45
echo "=== DONE"
