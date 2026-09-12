#!/usr/bin/env bash
# 远端 v52 验证：位精确（本地更严套件）+ 同节点交替 A/B（v52 vs v51-ours vs v50-base）× DDR/HBM 两种内存模式 + 官方 bench
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
[[ -f build/conv2d_v52.c && -f build/conv2d_v50.c ]] || { echo "缺基线/候选源"; exit 1; }
gcc $F tools/test_conv.c build/conv2d_v52.c -o build/tc52 -lm 2>&1 | grep -iE "error|warning" | head
gcc $F tools/fbench.c build/conv2d_v52.c -o build/fb52 -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c conv2d.c -o build/fb51 -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c build/conv2d_v50.c -o build/fb50 -lm 2>&1 | grep -iE "error"
gcc $F bench_conv.c build/conv2d_v52.c -o build/off52 -lm 2>&1 | grep -iE "error"
for b in tc52 fb52 fb51 fb50 off52; do [[ -x build/$b ]] || { echo "BUILD FAIL $b"; exit 1; }; done
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
echo "--- v52 位精确（默认 80 / ROLL=0 / ROLL=1，本地严套件含 KH16-30、129/257）"
numactl -N 1 build/tc52 80 4101 2>&1 | tail -1
CONV_ROLL=0 numactl -N 1 build/tc52 40 4102 2>&1 | tail -1
CONV_ROLL=1 numactl -N 1 build/tc52 40 4103 2>&1 | tail -1
HB=""; numactl -N 1 --preferred=17 true >/dev/null 2>&1 && HB="--preferred=17"
for mode in "" "$HB"; do
  [[ -z "$mode" ]] && tag=DDR || tag=HBM
  [[ "$tag" == HBM && -z "$HB" ]] && continue
  echo "--- A/B $tag（交替，best of 3 calls）"
  for r in 1 2 3; do
    for args in "4096 6144 39 39" "6144 4096 41 41"; do
      printf "%-4s r%d v52 %-16s " $tag $r "$args"; numactl -N 1 $mode build/fb52 $args 3 2>&1 | tail -1
      printf "%-4s r%d v51 %-16s " $tag $r "$args"; numactl -N 1 $mode build/fb51 $args 3 2>&1 | tail -1
      printf "%-4s r%d v50 %-16s " $tag $r "$args"; numactl -N 1 $mode build/fb50 $args 3 2>&1 | tail -1
    done
  done
  for args in "4256 6390 55 55" "6390 4256 81 81"; do
    printf "%-4s r1 v52 %-16s " $tag "$args"; numactl -N 1 $mode build/fb52 $args 3 2>&1 | tail -1
    printf "%-4s r1 v51 %-16s " $tag "$args"; numactl -N 1 $mode build/fb51 $args 3 2>&1 | tail -1
    printf "%-4s r1 v50 %-16s " $tag "$args"; numactl -N 1 $mode build/fb50 $args 3 2>&1 | tail -1
  done
done
echo "--- 官方 bench v52（-march，DDR node1）"
for a in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 1 build/off52 $a 2>&1 | grep -E "PASS|FAIL" | tail -1; done
echo "=== DONE"; date
