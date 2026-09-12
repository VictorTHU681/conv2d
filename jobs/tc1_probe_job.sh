#!/usr/bin/env bash
# TC1（k39）线上劣化归因：本地内存 vs 远端内存代理（numactl -m 0 放大延迟），
# 对比 nf=4（现状 pairf4+K4(3)）/ nf=3（pairf3+K4(4) 满槽）/ nf=0（8×2(7) 无 K4）/ 经典内核，
# CONV_ROLL_DIAG=1 输出各内核种类的周期/tile步。k41 作对照（线上正常）。
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
gcc $F tools/fbench.c conv2d.c -o build/fbench -lm 2>&1 | grep -iE "error"
[[ -x build/fbench ]] || { echo BUILD FAIL; exit 1; }
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
run1() { # $1 标签 $2 内存参数 $3 环境串 $4 形状
  printf "%-26s " "$1"
  env $3 CONV_ROLL_DIAG=1 numactl -N 1 $2 build/fbench $4 3 2>&1 | grep -E "best|^\[roll\]" | tail -2 | tr '\n' ' ' ; echo
}
for mem in "" "-m 0"; do
  tag=$([ -z "$mem" ] && echo local || echo remote)
  echo "--- k39 $tag"
  for r in 1 2; do
    run1 "[$tag nf4  r$r]" "$mem" "X=0"        "4096 6144 39 39"
    run1 "[$tag nf3  r$r]" "$mem" "CONV_NF=3"  "4096 6144 39 39"
    run1 "[$tag nf0  r$r]" "$mem" "CONV_NF=0"  "4096 6144 39 39"
    run1 "[$tag cls  r$r]" "$mem" "CONV_ROLL=0" "4096 6144 39 39"
  done
  echo "--- k41 $tag（对照）"
  run1 "[$tag k41  r1]" "$mem" "X=0" "6144 4096 41 41"
done
echo "=== DONE"; date
