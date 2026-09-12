#!/usr/bin/env bash
# 诊断包生成与验收：mkdiag.py 注入 → 编译（-DCONV_DIAG_ONLINE）→ 位精确（CONV_DIAG=0 静默 + =1 冒烟）
# → 官方 bench 看 PASS 与 [conv-diag] 输出 → 打包 conv_diag.zip → 端到端解压 bash run.sh
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"
mkdir -p build
python3 tools/mkdiag.py conv2d.c build/conv2d_diag.c || { echo "MKDIAG FAIL"; exit 1; }
gcc $F -DCONV_DIAG_ONLINE tools/test_conv.c build/conv2d_diag.c -o build/tc_d -lm 2>&1 | grep -iE "error|warning" | head
gcc $F -DCONV_DIAG_ONLINE bench_conv.c build/conv2d_diag.c -o build/bd -lm 2>&1 | grep -iE "error"
gcc -O3 -DCONV_DIAG_ONLINE bench_conv.c build/conv2d_diag.c -o build/bd_plain -lm -fopenmp 2>&1 | grep -iE "error"
for b in tc_d bd bd_plain; do [[ -x build/$b ]] || { echo "BUILD FAIL $b"; exit 1; }; done
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
echo "--- 位精确（CONV_DIAG=0 静默，80 例）"
CONV_DIAG=0 numactl -N 1 build/tc_d 60 3201 2>&1 | grep -E "ALL PASS|FAIL"
echo "--- 位精确（CONV_DIAG=1 冒烟 3 例，看输出格式）"
numactl -N 1 build/tc_d 3 3202 2>&1 | tail -6
echo "--- 官方 bench 诊断构建（-march，k39 与 k81）"
for a in "4096 6144 39 39 1" "6390 4256 81 81 1"; do numactl -N 1 build/bd $a 2>&1 | grep -E "PASS|FAIL|conv-diag"; echo; done
echo "--- 官方 bench 诊断构建（无 -march 题面命令，k39）"
numactl -N 1 build/bd_plain 4096 6144 39 39 1 2>&1 | grep -E "PASS|FAIL" | tail -1
# 打包
TMP=$(mktemp -d /tmp/mkdiag.XXXX); D="$TMP/conv"; mkdir -p "$D"
cp bench_conv.c README.md "$D/"; cp build/conv2d_diag.c "$D/conv2d.c"; cp run_diag.sh "$D/run.sh"; chmod +x "$D/run.sh"
(cd "$TMP" && zip -q -r out.zip conv) && cp "$TMP/out.zip" submissions/conv_diag.zip
echo "packed submissions/conv_diag.zip md5=$(md5sum submissions/conv_diag.zip | cut -d' ' -f1)"
rm -rf "$TMP"
echo "--- 端到端解压 bash run.sh（诊断包全流程）"
Z=$(mktemp -d /tmp/zd.XXXX)
(cd "$Z" && unzip -q "$OLDPWD/submissions/conv_diag.zip" && cd conv && unset OMP_NUM_THREADS OMP_PROC_BIND OMP_PLACES OMP_DYNAMIC && bash ./run.sh 2>&1 | grep -E "run-diag|conv-diag|PASS|FAIL" | head -46)
rm -rf "$Z"
echo "=== DONE"; date
