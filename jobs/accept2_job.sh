#!/usr/bin/env bash
# 两个提交包验收：conv.zip（v43 语义）与 conv_zva.zip（对照）
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
for Z in conv_diag.zip conv_diag_zva.zip; do
  echo "##### $Z ($(md5sum submissions/$Z | cut -c1-8))"
  T=$(mktemp -d /tmp/convzip.XXXX); Z0="$PWD/submissions/$Z"
  (cd "$T" && unzip -q "$Z0"; cd conv && unset OMP_NUM_THREADS OMP_PROC_BIND OMP_PLACES OMP_DYNAMIC && bash ./run.sh 2>&1 | grep -E "PASS|FAIL|Error|run.sh|conv-diag|run-diag")
  echo "--- 判题命令 ×1"
  for args in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do OMP_NUM_THREADS=38 numactl -N 1 "$T/conv/conv2d_test" $args 2>&1 | grep -E "PASS|FAIL" | tail -1; done
  rm -rf "$T"
done
echo "=== DONE"; date
