#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build; gcc -O2 -march=armv9-a+sve2 -fopenmp probe/zva.c -o build/zva 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores
numactl -N 1 -m 1 build/zva $((32<<20))
echo "--- 19 线程"; OMP_NUM_THREADS=19 numactl -N 1 -m 1 build/zva $((32<<20))
echo "=== DONE"; date
