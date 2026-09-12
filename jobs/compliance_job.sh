#!/usr/bin/env bash
# 合规整改验证（v51）：泛化位精确（含滚动全分组段）+ 同节点交替 A/B（v51 vs v50 基线）+ 官方 bench 两种编译
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
[[ -f build/conv2d_v50.c ]] || { echo "缺少基线 build/conv2d_v50.c"; exit 1; }
gcc $F tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning" | head -20
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
gcc $F bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE "error"
gcc -O3 bench_conv.c conv2d.c -o build/conv2d_test_plain -lm -fopenmp 2>&1 | grep -iE "error"
gcc $F tools/fbench.c build/conv2d_v50.c -o build/fbench_v50 -lm 2>&1 | grep -iE "error"
for b in test_conv fbench conv2d_test conv2d_test_plain fbench_v50; do [[ -x build/$b ]] || { echo "BUILD FAIL $b"; exit 1; }; done
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
echo "--- 泛化位精确（默认新随机带 KH16-90 / ROLL=0 / ROLL=1 / SWDENSE / STORE / SP / 5、1 线程 / BR=0 / POOL=0 / 通用回退）"
numactl -N 1 build/test_conv 150 2401 2>&1 | tail -1
CONV_ROLL=0 numactl -N 1 build/test_conv 60 2402 2>&1 | tail -1
CONV_ROLL=1 numactl -N 1 build/test_conv 60 2403 2>&1 | tail -1
CONV_SWDENSE=0 numactl -N 1 build/test_conv 40 2404 2>&1 | tail -1
CONV_SWDENSE=1 numactl -N 1 build/test_conv 40 2405 2>&1 | tail -1
CONV_STORE=0 numactl -N 1 build/test_conv 40 2406 2>&1 | tail -1
CONV_SP=1 numactl -N 1 build/test_conv 40 2407 2>&1 | tail -1
CONV_SP=3 numactl -N 1 build/test_conv 40 2408 2>&1 | tail -1
OMP_NUM_THREADS=5 numactl -N 1 build/test_conv 40 2409 2>&1 | tail -1
OMP_NUM_THREADS=1 numactl -N 1 build/test_conv 12 2410 2>&1 | tail -1
CONV_BR=0 numactl -N 1 build/test_conv 30 2411 2>&1 | tail -1
CONV_POOL=0 numactl -N 1 build/test_conv 30 2412 2>&1 | tail -1
CONV_NO_SME=1 numactl -N 1 build/test_conv 20 2413 2>&1 | tail -1
echo "--- fbench 交替 A/B x3（v51 vs v50，同节点）"
for r in 1 2 3; do
  for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
    printf "## r%d v51 %-18s " $r "$args"; numactl -N 1 build/fbench $args 3 2>&1 | tail -1
    printf "## r%d v50 %-18s " $r "$args"; numactl -N 1 build/fbench_v50 $args 3 2>&1 | tail -1
  done
done
echo "--- 官方 bench（-march）"
for args in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 1 build/conv2d_test $args 2>&1 | grep -E "PASS|FAIL" | tail -1; done
echo "--- 官方 bench（题面参考编译命令，无 -march）"
for args in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 1 build/conv2d_test_plain $args 2>&1 | grep -E "PASS|FAIL" | tail -1; done
echo "=== DONE"; date
