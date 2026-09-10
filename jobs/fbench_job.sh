#!/usr/bin/env bash
# 快速判题口径：四例 ×3（参考哈希缓存在 refcache/，首次会算一次官方参考）
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error" && exit 1
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do numactl -N 1 build/fbench $args ${RUNS:-3} 2>&1 | tail -1; done
echo "=== DONE"; date
