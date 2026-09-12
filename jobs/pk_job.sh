#!/usr/bin/env bash
# k41 打包残余定位：v51 默认（并行打包）vs CONV_PACKSER=1（主线程串行打包）vs v50 基线，带 CONV_ROLL_DIAG 内核分解
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c build/conv2d_v50.c -o build/fbench_v50 -lm 2>&1 | grep -iE "error"
[[ -x build/fbench && -x build/fbench_v50 ]] || { echo BUILD FAIL; exit 1; }
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
for args in "6144 4096 41 41" "4096 6144 39 39"; do
  for r in 1 2; do
    echo "## v51-par $args r$r";  CONV_ROLL_DIAG=1 numactl -N 1 build/fbench $args 3 2>&1 | grep -E "best|^\[roll\]" | tail -2
    echo "## v51-ser $args r$r";  CONV_PACKSER=1 CONV_ROLL_DIAG=1 numactl -N 1 build/fbench $args 3 2>&1 | grep -E "best|^\[roll\]" | tail -2
    echo "## v50     $args r$r";  CONV_ROLL_DIAG=1 numactl -N 1 build/fbench_v50 $args 3 2>&1 | grep -E "best|^\[roll\]" | tail -2
  done
done
echo "=== DONE"; date
