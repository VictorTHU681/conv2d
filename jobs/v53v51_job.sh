#!/usr/bin/env bash
# v53 vs 合规 v51（上一个无打包缓存版本，commit c2a418e 源）同节点交替 A/B：DDR 与 HBM 各 3 轮
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
gcc $F tools/fbench.c build/conv2d_v51.c -o build/fb51 -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c conv2d.c -o build/fb53x -lm 2>&1 | grep -iE "error"
for b in fb51 fb53x; do [[ -x build/$b ]] || { echo "BUILD FAIL $b"; exit 1; }; done
md5sum conv2d.c build/conv2d_v51.c
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
HB=""; numactl -N 1 --preferred=17 true >/dev/null 2>&1 && HB="--preferred=17"
for tag in DDR HBM; do
  if [[ $tag == DDR ]]; then mode=""; else [[ -z "$HB" ]] && continue; mode="$HB"; fi
  echo "--- A/B $tag（v53 / v51 交替 ×3）"
  for r in 1 2 3; do
    for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
      printf "%-4s r%d v53 %-16s " $tag $r "$args"; numactl -N 1 $mode build/fb53x $args 3 2>&1 | tail -1
      printf "%-4s r%d v51 %-16s " $tag $r "$args"; numactl -N 1 $mode build/fb51 $args 3 2>&1 | tail -1
    done
  done
done
echo "=== DONE"; date
