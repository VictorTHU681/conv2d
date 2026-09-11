#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O1 -g -march=armv9-a+sme+sve2 -fopenmp tools/fbench.c conv2d.c -o build/fbench_g -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
ulimit -c 0
echo "--- fbench k39 roll (1 thread)"; OMP_NUM_THREADS=1 CONV_ROLL=1 CONV_POOL=0 timeout 120 numactl -N 5 build/fbench_g 1024 2048 39 39 1; echo "exit=$?"
echo "--- fbench k39 roll (38 threads, no pool)"; CONV_ROLL=1 CONV_POOL=0 timeout 120 numactl -N 5 build/fbench_g 4096 6144 39 39 1; echo "exit=$?"
echo "--- fbench k39 roll (38 threads, pool)"; CONV_ROLL=1 timeout 120 numactl -N 5 build/fbench_g 4096 6144 39 39 1; echo "exit=$?"
echo "--- gdb batch on crash"; CONV_ROLL=1 CONV_POOL=0 OMP_NUM_THREADS=1 timeout 300 gdb -batch -ex run -ex bt -ex "info registers pc" --args build/fbench_g 1024 2048 39 39 1 2>&1 | tail -25
echo "=== DONE"
