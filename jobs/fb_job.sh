#!/usr/bin/env bash
# 快速迭代：fbench（参考哈希缓存，逐位比对）
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp -Wall tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error|warning"
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
R="numactl -N 5 --preferred=21"
if [[ -z "$NOGEN" ]]; then echo "--- 泛化 CONV_ROLL=1 与 CONV_ROLL=1+DIRECT"; CONV_ROLL=1 $R build/test_conv ${NGEN:-40} 2>&1 | grep -E "FAIL|PASS"; CONV_ROLL=1 CONV_ROLL_DIRECT=1 $R build/test_conv ${NGEN:-40} 7 2>&1 | grep -E "FAIL|PASS"; fi
for mode in "" "CONV_ROLL_DIRECT=1"; do
  echo "--- 滚动 $mode"
  for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55"; do
    env CONV_ROLL=1 CONV_ROLL_DIAG=1 $mode $R build/fbench $args 3 2>&1 | grep -E "best|\[roll\]" | tail -2
  done
done
if [[ -z "$NOBASE" ]]; then echo "--- 经典 基线"
for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55"; do CONV_ROLL=0 $R build/fbench $args 3 2>&1 | tail -1; done; fi
for e in ${EXTRA:-}; do echo "--- $e"; for args in "4096 6144 39 39" "6144 4096 41 41"; do env CONV_ROLL=1 CONV_ROLL_DIAG=1 $e $R build/fbench $args 3 2>&1 | grep -E "best|\[roll\]" | tail -2; done; done
echo "=== DONE"; date; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
