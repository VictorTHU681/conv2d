#!/usr/bin/env bash
# 正式版验证：编译告警、node5 上的泛化测试、run.sh 全流程（node5 + HBM）、判题命令对照
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F -Wall tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc $F bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
echo "--- 泛化 node5"; numactl -N 5 build/test_conv 150 1911 2>&1 | grep -E "FAIL|PASS"
CONV_BR=0 numactl -N 5 build/test_conv 30 1912 2>&1 | grep -E "FAIL|PASS"
CONV_STORE=0 numactl -N 5 build/test_conv 30 1913 2>&1 | grep -E "FAIL|PASS"
CONV_SP=1 numactl -N 5 build/test_conv 30 1914 2>&1 | grep -E "FAIL|PASS"
OMP_NUM_THREADS=5 numactl -N 5 build/test_conv 30 1915 2>&1 | grep -E "FAIL|PASS"
OMP_NUM_THREADS=1 numactl -N 5 build/test_conv 12 1916 2>&1 | grep -E "FAIL|PASS"
CONV_NO_SME=1 numactl -N 5 build/test_conv 20 1917 2>&1 | grep -E "FAIL|PASS"
echo "--- 官方 bench node5 + HBM21 ×2"
for r in 1 2; do for args in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 5 --preferred=21 build/conv2d_test $args 2>&1 | grep -E "PASS|FAIL" | tail -1; done; done
echo "--- 提交包 run.sh 全流程（无预设 OMP 环境）"
T=$(mktemp -d /tmp/convzip.XXXX); Z0="$PWD/submissions/conv.zip"
(cd "$T" && unzip -q "$Z0" && cd conv && unset OMP_NUM_THREADS OMP_PROC_BIND OMP_PLACES OMP_DYNAMIC && bash ./run.sh 2>&1 | grep -E "PASS|FAIL|Error|run.sh")
rm -rf "$T"
echo "=== DONE"; date
