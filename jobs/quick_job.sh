#!/usr/bin/env bash
# 快速：泛化（默认）+ fbench ×3 + 分相（含 enter max）
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc $F tools/drv.c conv2d.c -o build/drv -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
numactl -N 1 build/test_conv 100 1501 2>&1 | grep -E "FAIL|PASS"
OMP_NUM_THREADS=5 numactl -N 1 build/test_conv 30 1502 2>&1 | grep -E "FAIL|PASS"
for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do numactl -N 1 build/fbench $args 3 2>&1 | tail -1; done
for c in "4096 6144 39 39" "6390 4256 81 81"; do echo "##### $c"; CONV_PROFILE=1 numactl -N 1 build/drv $c 3 2>&1 | grep -E "conv prof" | tail -2 | sed -E "s/\| pre [0-9.]+ ms //"; done
echo "=== DONE"; date
