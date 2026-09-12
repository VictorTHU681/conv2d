#!/usr/bin/env bash
# 定夺重叠打包默认值：v54-ovl（默认 ps1）/ v54-ser（PACKSER=2 不重叠）/ v53 三方交替，HBM 为主
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
gcc $F tools/fbench.c conv2d.c -o build/fb54 -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c build/conv2d_v53.c -o build/fb53 -lm 2>&1 | grep -iE "error"
for b in fb54 fb53; do [[ -x build/$b ]] || { echo "BUILD FAIL $b"; exit 1; }; done
md5sum conv2d.c
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
HB=""; numactl -N 1 --preferred=17 true >/dev/null 2>&1 && HB="--preferred=17"
echo "--- HBM 三方交替 ×4（k39/k41），×2（k55/k81）"
for r in 1 2 3 4; do
  for args in "4096 6144 39 39" "6144 4096 41 41"; do
    printf "r%d ovl %-16s " $r "$args"; numactl -N 1 $HB build/fb54 $args 3 2>&1 | tail -1
    printf "r%d ser %-16s " $r "$args"; CONV_PACKSER=2 numactl -N 1 $HB build/fb54 $args 3 2>&1 | tail -1
    printf "r%d v53 %-16s " $r "$args"; numactl -N 1 $HB build/fb53 $args 3 2>&1 | tail -1
  done
done
for r in 1 2; do
  for args in "4256 6390 55 55" "6390 4256 81 81"; do
    printf "r%d ovl %-16s " $r "$args"; numactl -N 1 $HB build/fb54 $args 3 2>&1 | tail -1
    printf "r%d ser %-16s " $r "$args"; CONV_PACKSER=2 numactl -N 1 $HB build/fb54 $args 3 2>&1 | tail -1
    printf "r%d v53 %-16s " $r "$args"; numactl -N 1 $HB build/fb53 $args 3 2>&1 | tail -1
  done
done
echo "=== DONE"; date
