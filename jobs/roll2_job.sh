#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp probe/roll2.c -o build/roll2 -lm 2>&1 | grep -iE "error|warning"
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE "error"
export OMP_PROC_BIND=close OMP_PLACES=cores
echo "--- 旧内核基线（同节点同频）"; OMP_NUM_THREADS=38 numactl -N 5 --preferred=21 build/conv2d_test 4096 6144 39 39 1 | grep -E "PASS|FAIL"
OMP_NUM_THREADS=38 numactl -N 5 --preferred=21 build/conv2d_test 6144 4096 41 41 1 | grep -E "PASS|FAIL"
echo "--- 各内核在 38 线程满载下的速度"
for o in 32 8; do echo "ONLY=$o k39"; THR=1 ONLY=$o numactl -N 5 --preferred=21 build/roll2 4096 6144 39 39 38 0 | grep -E "rep 2|^   "; done
for o in 32 8 1; do echo "ONLY=$o k41"; THR=1 ONLY=$o numactl -N 5 --preferred=21 build/roll2 6144 4096 41 41 38 0 | grep -E "rep 2|^   "; done
echo "ONLY=1 k81"; ONLY=1 numactl -N 5 --preferred=21 build/roll2 6390 4256 81 81 38 0 | grep -E "rep 2"
echo "ONLY=16 k55"; THR=1 ONLY=16 numactl -N 5 --preferred=21 build/roll2 4256 6390 55 55 38 0 | grep -E "rep 2|^   "
echo "ONLY=32 k81"; ONLY=32 numactl -N 5 --preferred=21 build/roll2 6390 4256 81 81 38 0 | grep -E "rep 2"
echo "--- 全流程 校验 + 静态/动态"
for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
  echo "--- $args static"; numactl -N 5 --preferred=21 build/roll2 $args 38 1 | grep -E "groups|rep 2|best|correctness"
  echo "--- $args static W2=1.3"; W2=1.3 numactl -N 5 --preferred=21 build/roll2 $args 38 0 | grep -E "rep 2|best"
done
echo "--- PD 扫描 k39 static"
for pd in 2 3 4 5; do PD=$pd numactl -N 5 --preferred=21 build/roll2 4096 6144 39 39 38 0 | grep -E "best"; done
echo "=== DONE"; date; cat /sys/devices/system/cpu/cpu190/cpufreq/scaling_cur_freq
