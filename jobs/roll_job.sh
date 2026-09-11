#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp probe/roll.c -o build/roll -lm 2>&1 | grep -iE "error|warning"
export OMP_PROC_BIND=close OMP_PLACES=cores
echo "--- k39 4096x6144"; numactl -N 5 --preferred=21 build/roll 4096 6144 39 39 38
echo "--- k41 6144x4096"; numactl -N 5 --preferred=21 build/roll 6144 4096 41 41 38
echo "--- k81 6390x4256"; numactl -N 5 --preferred=21 build/roll 6390 4256 81 81 38
echo "=== DONE"; date
