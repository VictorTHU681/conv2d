#!/usr/bin/env bash
# 生成线上 A/B 对照包：conv.zip（k39 nf4，当前默认）与 conv_nf3.zip（k39 nf3，run.sh 编译加 -DCONV_NF_REM7=3）。
# 两包 conv2d.c/bench_conv.c/README 逐字节相同，唯一差别是 B 包 run.sh 的编译标志。先各自验收（位精确 + 官方 bench）。
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
# 位精确 + 官方 bench：A（默认 nf4）与 B（-DCONV_NF_REM7=3）
gcc $F                    tools/test_conv.c conv2d.c -o build/tc_a -lm 2>&1 | grep -iE "error|warning" | head
gcc $F -DCONV_NF_REM7=3   tools/test_conv.c conv2d.c -o build/tc_b -lm 2>&1 | grep -iE "error|warning" | head
gcc $F                    bench_conv.c conv2d.c -o build/ba -lm 2>&1 | grep -iE "error"
gcc $F -DCONV_NF_REM7=3   bench_conv.c conv2d.c -o build/bb -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
echo "--- 泛化位精确 A（nf4 默认）"; numactl -N 1 build/tc_a 80 3101 2>&1 | tail -1
echo "--- 泛化位精确 B（nf3）";      numactl -N 1 build/tc_b 80 3102 2>&1 | tail -1
echo "--- 官方 bench A（nf4）"; for a in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 1 build/ba $a 2>&1 | grep -E "PASS|FAIL" | tail -1; done
echo "--- 官方 bench B（nf3，仅 k39 应变化，其余不变）"; for a in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do numactl -N 1 build/bb $a 2>&1 | grep -E "PASS|FAIL" | tail -1; done
# 打包
TMP=$(mktemp -d /tmp/mkpair.XXXX)
for V in a b; do
  D="$TMP/conv"; rm -rf "$D"; mkdir -p "$D"
  cp bench_conv.c conv2d.c README.md "$D/"
  if [[ $V == a ]]; then cp run.sh "$D/run.sh"; else
    # B 包：SME 主编译加 -DCONV_NF_REM7=3
    sed 's#-march=armv9-a+sme+sve2 -fopenmp bench_conv.c#-march=armv9-a+sme+sve2 -DCONV_NF_REM7=3 -fopenmp bench_conv.c#' run.sh > "$D/run.sh"
  fi
  chmod +x "$D/run.sh"
  OUT=$([[ $V == a ]] && echo submissions/conv.zip || echo submissions/conv_nf3.zip)
  (cd "$TMP" && rm -f out.zip && zip -q -r out.zip conv) && cp "$TMP/out.zip" "$OUT"
  echo "packed $OUT md5=$(md5sum "$OUT" | cut -d' ' -f1)"
  grep -n "CONV_NF_REM7\|march=armv9" "$D/run.sh" | head
done
rm -rf "$TMP"
echo "=== DONE"; date
