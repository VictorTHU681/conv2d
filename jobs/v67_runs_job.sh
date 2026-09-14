#!/usr/bin/env bash
# v67 定稿验证：官方 bench 口径下 runs=50（平均）与 runs=1（单次）成绩对比 + 清理版源码正确性。
# 用与 run.sh 相同的编译命令与绑定方式。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

cd "$(dirname "$0")/.."
sha256sum conv2d.c bench_conv.c
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o /tmp/conv2d_test_v67 -lm
echo BUILD-OK

for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    for r in 1 1 50; do
        printf "RUNS shape=%s r=%s " "$args" "$r"
        "${run[@]}" /tmp/conv2d_test_v67 "${shape[@]}" "$r" 2>&1 | tail -1
    done
done
echo "V67_RUNS_DONE $(date -Is)"
