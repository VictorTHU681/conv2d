#!/usr/bin/env bash
# 完整验证：泛化位精确（多种环境变量变体）+ 快速 bench ×3 + 分相 + 官方 bench（两种编译命令）
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
gcc $F tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc $F tools/drv.c conv2d.c -o build/drv -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
gcc $F bench_conv.c conv2d.c -o build/conv2d_test -lm 2>&1 | grep -iE "error"
gcc -O3 bench_conv.c conv2d.c -o build/conv2d_test_plain -lm -fopenmp 2>&1 | grep -iE "error"
for b in test_conv drv fbench conv2d_test conv2d_test_plain; do [[ -x build/$b ]] || { echo "BUILD FAIL $b"; exit 1; }; done
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
echo "--- 泛化（默认 / SWDENSE=0 / SWDENSE=1 / STORE=0 / SP=1 / SP=3 / 5 线程 / 1 线程 / BR=0 / POOL=0 / 通用回退）"
numactl -N 1 build/test_conv 150 1401 2>&1 | grep -E "FAIL|PASS"
CONV_SWDENSE=0 numactl -N 1 build/test_conv 40 1402 2>&1 | grep -E "FAIL|PASS"
CONV_SWDENSE=1 numactl -N 1 build/test_conv 40 1403 2>&1 | grep -E "FAIL|PASS"
CONV_STORE=0 numactl -N 1 build/test_conv 40 1404 2>&1 | grep -E "FAIL|PASS"
CONV_SP=1 numactl -N 1 build/test_conv 40 1405 2>&1 | grep -E "FAIL|PASS"
CONV_SP=3 numactl -N 1 build/test_conv 40 1406 2>&1 | grep -E "FAIL|PASS"
OMP_NUM_THREADS=5 numactl -N 1 build/test_conv 40 1407 2>&1 | grep -E "FAIL|PASS"
OMP_NUM_THREADS=1 numactl -N 1 build/test_conv 12 1408 2>&1 | grep -E "FAIL|PASS"
CONV_BR=0 numactl -N 1 build/test_conv 30 1409 2>&1 | grep -E "FAIL|PASS"
CONV_POOL=0 numactl -N 1 build/test_conv 30 1410 2>&1 | grep -E "FAIL|PASS"
CONV_NO_SME=1 numactl -N 1 build/test_conv 20 1411 2>&1 | grep -E "FAIL|PASS"
echo "--- fbench 四例 ×3（cur vs v42 基线，同节点）"
[ -f build/conv2d_v42.c ] && gcc $F tools/fbench.c build/conv2d_v42.c -o build/fbench_v42 -lm 2>&1 | grep -iE "error"
for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
  echo "## cur $args"; numactl -N 1 build/fbench $args 3 2>&1 | tail -1 | sed -E "s/.*best/  best/"
  [ -x build/fbench_v42 ] && { echo "## v42 $args"; numactl -N 1 build/fbench_v42 $args 3 2>&1 | tail -1 | sed -E "s/.*best/  best/"; }
done
echo "--- 分相"
run() { echo "##### $1"; shift; numactl -N 1 build/drv "$@" 3 2>&1 | grep -E "conv prof" | sed -E "s/.*br ([0-9]+\/[0-9]+).*region ([0-9.]+) ms.*avg\/max ([0-9.]+)\/([0-9.]+)\/([0-9.]+) \| build ([0-9.]+)\/[0-9.]+ \| kern ([0-9.]+)\/[0-9.]+ \| store ([0-9.]+).*/  br \1 region \2 avg \4 kern \7 store \8/" | tail -2; }
for c in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do CONV_PROFILE=1 run "$c" $c; done
echo "--- 官方 bench（-march）"
for args in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 1 build/conv2d_test $args 2>&1 | grep -E "PASS|FAIL" | tail -1; done
echo "--- 官方 bench（题面参考编译命令，无 -march）"
for args in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 1 build/conv2d_test_plain $args 2>&1 | grep -E "PASS|FAIL" | tail -1; done
echo "=== DONE"; date
