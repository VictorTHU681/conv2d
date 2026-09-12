#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
hostname
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp probe/pfdbg.c conv2d.c -o build/pfdbg -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores
echo "--- 200x900 55x55"; CONV_ROLL=1 numactl -N 5 build/pfdbg 200 900 55 55
echo "--- 150x800 55x23"; CONV_ROLL=1 numactl -N 5 build/pfdbg 150 800 55 23
echo "--- 190x900 87x33"; CONV_ROLL=1 numactl -N 5 build/pfdbg 190 900 87 33
echo DONE
