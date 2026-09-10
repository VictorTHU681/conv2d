#!/usr/bin/env bash
# 边界行 fmla 方案：fmla 步与 1x4+ext 步交错的干扰曲线
cd "$(dirname "$0")/../probe" || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
gcc -O2 -march=armv9-a+sme+sve2 brmix.c -o brmix 2>&1 | grep -iE "error" && exit 1
for c in 40 41; do echo "##### cpu $c"; taskset -c $c ./brmix; done
echo "=== DONE"; date
