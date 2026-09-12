#!/usr/bin/env bash
# v53 全量验证：严格位精确（含 TEST_SIGNED/TEST_BITWISE/TEST_REUSE_HEIGHT）+ 三方 A/B（v53/v52/v50 × DDR/HBM）+ 官方两种编译
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
gcc $F tools/test_conv.c conv2d.c -o build/tc53 -lm 2>&1 | grep -iE "error|warning" | head
gcc $F tools/fbench.c conv2d.c -o build/fb53 -lm 2>&1 | grep -iE "error"
gcc $F bench_conv.c conv2d.c -o build/off53 -lm 2>&1 | grep -iE "error"
gcc -O3 bench_conv.c conv2d.c -o build/off53p -lm -fopenmp 2>&1 | grep -iE "error"
for b in tc53 fb53 off53 off53p fb52 fb50; do [[ -x build/$b ]] || { echo "BUILD FAIL $b"; exit 1; }; done
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
echo "--- 位精确：默认 / ROLL=0 / ROLL=1 / SIGNED / BITWISE / BITWISE+SIGNED / REUSE_HEIGHT / NF=3 / 通用回退"
numactl -N 1 build/tc53 80 5101 2>&1 | tail -1
CONV_ROLL=0 numactl -N 1 build/tc53 40 5102 2>&1 | tail -1
CONV_ROLL=1 numactl -N 1 build/tc53 40 5103 2>&1 | tail -1
TEST_SIGNED=1 numactl -N 1 build/tc53 40 5104 2>&1 | tail -1
TEST_BITWISE=1 numactl -N 1 build/tc53 40 5105 2>&1 | tail -1
TEST_BITWISE=1 TEST_SIGNED=1 numactl -N 1 build/tc53 40 5106 2>&1 | tail -1
TEST_REUSE_HEIGHT=1 numactl -N 1 build/tc53 10 5107 2>&1 | tail -1
CONV_NF=3 numactl -N 1 build/tc53 40 5108 2>&1 | tail -1
CONV_NO_SME=1 numactl -N 1 build/tc53 20 5109 2>&1 | tail -1
HB=""; numactl -N 1 --preferred=17 true >/dev/null 2>&1 && HB="--preferred=17"
for mode in "" "$HB"; do
  [[ -z "$mode" ]] && tag=DDR || tag=HBM
  [[ "$tag" == HBM && -z "$HB" ]] && continue
  echo "--- A/B $tag（v53 / v52 / v50 交替）"
  for r in 1 2; do
    for args in "4096 6144 39 39" "6144 4096 41 41"; do
      printf "%-4s r%d v53 %-16s " $tag $r "$args"; numactl -N 1 $mode build/fb53 $args 3 2>&1 | tail -1
      printf "%-4s r%d v52 %-16s " $tag $r "$args"; numactl -N 1 $mode build/fb52 $args 3 2>&1 | tail -1
      printf "%-4s r%d v50 %-16s " $tag $r "$args"; numactl -N 1 $mode build/fb50 $args 3 2>&1 | tail -1
    done
  done
  for args in "4256 6390 55 55" "6390 4256 81 81"; do
    printf "%-4s r1 v53 %-16s " $tag "$args"; numactl -N 1 $mode build/fb53 $args 3 2>&1 | tail -1
    printf "%-4s r1 v52 %-16s " $tag "$args"; numactl -N 1 $mode build/fb52 $args 3 2>&1 | tail -1
    printf "%-4s r1 v50 %-16s " $tag "$args"; numactl -N 1 $mode build/fb50 $args 3 2>&1 | tail -1
  done
done
echo "--- 官方 bench v53（-march / 无 -march，DDR node1）"
for a in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 1 build/off53 $a 2>&1 | grep -E "PASS|FAIL" | tail -1; done
for a in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 1 build/off53p $a 2>&1 | grep -E "PASS|FAIL" | tail -1; done
echo "=== DONE"; date
