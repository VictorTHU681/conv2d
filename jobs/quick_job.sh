#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F -DCONV_DIAG_ONLINE bench_conv.c conv2d.c -o build/conv2d_diag -lm 2>&1 | grep -iE "error|warning"
gcc $F bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
bash -c 'd() { echo "[run-diag] $*"; }; c1=38; b=/sys/devices/system/cpu/cpu38/cpufreq; d "cpu38 cpufreq: gov $(cat $b/scaling_governor 2>/dev/null) | cur $(cat $b/scaling_cur_freq 2>/dev/null) | hw_cur $(cat $b/cpuinfo_cur_freq 2>/dev/null) | setspeed $(cat $b/scaling_setspeed 2>/dev/null) | boost $(cat /sys/devices/system/cpu/cpufreq/boost 2>/dev/null)"; d "thermal: $(for t in /sys/class/thermal/thermal_zone*; do [ -d $t ] && printf "%s=%s " "$(cat $t/type 2>/dev/null)" "$(cat $t/temp 2>/dev/null)"; done 2>/dev/null | cut -c1-200)"; d "cppc cpu38: $(for f in highest_perf nominal_perf lowest_perf reference_perf nominal_freq lowest_freq; do printf "%s=%s " $f "$(cat /sys/devices/system/cpu/cpu38/acpi_cppc/$f 2>/dev/null)"; done)"'
for args in "4096 6144 39 39 1" "6390 4256 81 81 1"; do
  echo "##### diag $args"; numactl -N 1 build/conv2d_diag $args 2>&1 | grep -E "probes|burst|call 3|PASS|FAIL"
  echo "##### 无诊断 $args"; numactl -N 1 build/conv2d_test $args 2>&1 | grep -E "PASS|FAIL"
  echo "##### diag 19 线程 $args"; OMP_NUM_THREADS=19 numactl -N 1 build/conv2d_diag $args 2>&1 | grep -E "probes|burst|call 3|PASS|FAIL"
done
echo "=== DONE"; date
