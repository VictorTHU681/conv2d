#!/usr/bin/env bash
# A/B：默认 vs -DCONV_NO_SWPF（fbench 3 轮 best，两轮）
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
gcc $F -DCONV_NO_SWPF tools/fbench.c conv2d.c -o build/fbench_b -lm 2>&1 | grep -iE "error"
gcc $F tools/drv.c conv2d.c -o build/drv -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
numactl -N 1 build/test_conv 100 1601 2>&1 | grep -E "FAIL|PASS"
for r in 1 2; do for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
  echo "## A(swpf) $args"; numactl -N 1 build/fbench $args 3 2>&1 | tail -1 | sed -E "s/.*best/  best/"
  echo "## B(no)   $args"; numactl -N 1 build/fbench_b $args 3 2>&1 | tail -1 | sed -E "s/.*best/  best/"
done; done
for c in "4096 6144 39 39" "6390 4256 81 81"; do echo "##### $c"; CONV_PROFILE=1 numactl -N 1 build/drv $c 3 2>&1 | grep -E "conv prof" | tail -1 | sed -E "s/\| pre [0-9.]+ ms //"; done
echo "=== DONE"; date
