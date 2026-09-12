#!/usr/bin/env bash
# v54（打包提速：R 共享 + 对角构建 + kf st4）验证：位精确全套 + 打包相位剖析 + v54/v53 同节点交替 A/B + 官方两种编译
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
[[ -f build/conv2d_v53.c ]] || { echo "MISSING build/conv2d_v53.c"; exit 1; }
gcc $F tools/test_conv.c conv2d.c -o build/tc54 -lm 2>&1 | grep -iE "error|warning" | head
gcc $F tools/fbench.c conv2d.c -o build/fb54 -lm 2>&1 | grep -iE "error"
gcc $F tools/fbench.c build/conv2d_v53.c -o build/fb53 -lm 2>&1 | grep -iE "error"
gcc $F bench_conv.c conv2d.c -o build/off54 -lm 2>&1 | grep -iE "error"
gcc -O3 bench_conv.c conv2d.c -o build/off54p -lm -fopenmp 2>&1 | grep -iE "error"
for b in tc54 fb54 fb53 off54 off54p; do [[ -x build/$b ]] || { echo "BUILD FAIL $b"; exit 1; }; done
md5sum conv2d.c build/conv2d_v53.c
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
echo "--- 位精确：默认 / ROLL=0 / ROLL=1 / SIGNED / BITWISE / BITWISE+SIGNED / REUSE_HEIGHT / NF=3 / PACKSER=0 / PACKSER=1 / 通用回退"
numactl -N 1 build/tc54 80 5401 2>&1 | tail -1
CONV_ROLL=0 numactl -N 1 build/tc54 40 5402 2>&1 | tail -1
CONV_ROLL=1 numactl -N 1 build/tc54 40 5403 2>&1 | tail -1
TEST_SIGNED=1 numactl -N 1 build/tc54 40 5404 2>&1 | tail -1
TEST_BITWISE=1 numactl -N 1 build/tc54 40 5405 2>&1 | tail -1
TEST_BITWISE=1 TEST_SIGNED=1 numactl -N 1 build/tc54 40 5406 2>&1 | tail -1
TEST_REUSE_HEIGHT=1 numactl -N 1 build/tc54 10 5407 2>&1 | tail -1
CONV_NF=3 numactl -N 1 build/tc54 40 5408 2>&1 | tail -1
CONV_PACKSER=0 numactl -N 1 build/tc54 40 5409 2>&1 | tail -1
CONV_PACKSER=0 TEST_BITWISE=1 numactl -N 1 build/tc54 40 5410 2>&1 | tail -1
CONV_PACKSER=1 TEST_BITWISE=1 numactl -N 1 build/tc54 40 5411 2>&1 | tail -1
CONV_PACKSER=2 TEST_BITWISE=1 numactl -N 1 build/tc54 40 5413 2>&1 | tail -1
CONV_NO_SME=1 numactl -N 1 build/tc54 20 5412 2>&1 | tail -1
HB=""; numactl -N 1 --preferred=17 true >/dev/null 2>&1 && HB="--preferred=17"
echo "--- 打包相位（CONV_PROFILE=1，ps1 重叠串行 / ps2 串行不重叠，DDR）"
for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
  echo "## v54 ovl $args"; CONV_PROFILE=1 numactl -N 1 build/fb54 $args 2 2>&1 | grep -E "roll prof|best" | tail -4
  echo "## v54 ser $args"; CONV_PACKSER=2 CONV_PROFILE=1 numactl -N 1 build/fb54 $args 2 2>&1 | grep -E "roll prof|best" | tail -4
done
echo "--- W4 权重（HBM，117/123 交替 ×3）"
for r in 1 2 3; do
  printf "r%d W4=117 k39 " $r; CONV_ROLL_W4=117 numactl -N 1 $HB build/fb54 4096 6144 39 39 3 2>&1 | tail -1
  printf "r%d W4=123 k39 " $r; CONV_ROLL_W4=123 numactl -N 1 $HB build/fb54 4096 6144 39 39 3 2>&1 | tail -1
  printf "r%d W4=117 k55 " $r; CONV_ROLL_W4=117 numactl -N 1 $HB build/fb54 4256 6390 55 55 3 2>&1 | tail -1
  printf "r%d W4=123 k55 " $r; CONV_ROLL_W4=123 numactl -N 1 $HB build/fb54 4256 6390 55 55 3 2>&1 | tail -1
done
for tag in DDR HBM; do
  if [[ $tag == DDR ]]; then mode=""; else [[ -z "$HB" ]] && continue; mode="$HB"; fi
  echo "--- A/B $tag（v54 / v53 交替 ×3）"
  for r in 1 2 3; do
    for args in "4096 6144 39 39" "6144 4096 41 41" "4256 6390 55 55" "6390 4256 81 81"; do
      printf "%-4s r%d v54 %-16s " $tag $r "$args"; numactl -N 1 $mode build/fb54 $args 3 2>&1 | tail -1
      printf "%-4s r%d v53 %-16s " $tag $r "$args"; numactl -N 1 $mode build/fb53 $args 3 2>&1 | tail -1
    done
  done
done
echo "--- 官方 bench v54（-march / 无 -march，DDR node1）"
for a in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 1 build/off54 $a 2>&1 | grep -E "PASS|FAIL" | tail -1; done
for a in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 1 build/off54p $a 2>&1 | grep -E "PASS|FAIL" | tail -1; done
echo "=== DONE"; date
