#!/usr/bin/env bash
# 提交包验收：解压 ../submissions/conv.zip → bash run.sh（无预设 OMP 环境）→ 再用判题命令跑两轮
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
ZIP=${ZIP:-$PWD/submissions/conv.zip}
T=$(mktemp -d /tmp/convzip.XXXX)
(cd "$T" && unzip -q "$ZIP" && cd conv && unset OMP_NUM_THREADS OMP_PROC_BIND OMP_PLACES OMP_DYNAMIC && bash ./run.sh 2>&1 | grep -E "PASS|FAIL|Error|run.sh")
echo "--- 判题命令 ×2（提交包编出的二进制）"
for r in 1 2; do for args in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do
    OMP_NUM_THREADS=38 numactl -N 1 "$T/conv/conv2d_test" $args 2>&1 | grep -E "PASS|FAIL" | tail -1
done; done
rm -rf "$T"
echo "=== DONE"; date
