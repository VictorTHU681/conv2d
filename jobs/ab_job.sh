#!/usr/bin/env bash
# 验证 + 同节点三方 A/B：v42 / v43a（行首软流水） / cur（+ 无分支 sweep 收尾）
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F tools/test_conv.c conv2d.c -o build/test_conv -lm 2>&1 | grep -iE "error|warning"
gcc $F tools/fbench.c build/conv2d_v42.c -o build/fbench_v42 -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c build/conv2d_v43a.c -o build/fbench_a -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
numactl -N 1 build/test_conv 150 1706 2>&1 | grep -E "FAIL|PASS"
CONV_SWDENSE=1 numactl -N 1 build/test_conv 40 1707 2>&1 | grep -E "FAIL|PASS"
CONV_SP=1 numactl -N 1 build/test_conv 40 1708 2>&1 | grep -E "FAIL|PASS"
OMP_NUM_THREADS=5 numactl -N 1 build/test_conv 40 1709 2>&1 | grep -E "FAIL|PASS"
for r in 1 2 3; do for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
  for v in v42 a ""; do b=build/fbench${v:+_$v}; printf "## %-6s %-16s " "${v:-cur}" "$args"; numactl -N 1 $b $args 3 2>&1 | tail -1 | sed -E "s/.*best +[0-9.]+ ms +([0-9.]+) GFLOPS \| avg +[0-9.]+ ms +([0-9.]+) GFLOPS.*/best \1 avg \2/"; done
done; done
echo "=== DONE"; date
