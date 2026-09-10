#!/usr/bin/env bash
# CONV 赛题：编译 + 四组测试用例（判题系统直接执行本脚本）
set -o pipefail
cd "$(dirname "$0")" || exit 1

source /etc/profile >/dev/null 2>&1 || true
if [[ -d /home/HPC/HPCKit/latest/modulefiles ]]; then
    module use /home/HPC/HPCKit/latest/modulefiles 2>/dev/null
    module load gcc/compiler12.3.1/gccmodule 2>/dev/null
else
    for p in /work_ssd/software/HPCKit/latest/setvars.sh \
             /work_ssd/software/HPCKit/26.1.RC1/setvars.sh \
             /home/share/eapp_sysu/HPCKit/latest/setvars.sh \
             /home/share/eapp_sysu/HPCKit/26.1.RC1/setvars.sh; do
        if [[ -f "$p" ]]; then . "$p" --use-gcc >/dev/null 2>&1; break; fi
    done
fi

# 首选：SME FP32 fmopa 内核（需要支持 armv9-a+sme 的汇编器；运行期用 HWCAP2 检测硬件，缺失时自动回退 SVE 实现）。
# 若编译器不支持 SME，则编译纯 SVE/通用实现（保证正确性）。
rm -f conv2d_test
if ! gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o conv2d_test -lm 2>/dev/null; then
    echo "[run.sh] 编译器不支持 SME 扩展，回退通用实现" >&2
    if ! gcc -O3 -march=armv8.2-a+sve -fopenmp -DCONV_NO_SME_ASM bench_conv.c conv2d.c -o conv2d_test -lm 2>/dev/null; then
        gcc -O3 -fopenmp -DCONV_NO_SME_ASM bench_conv.c conv2d.c -o conv2d_test -lm
    fi
fi

# 判题口径：38 线程、单一 NUMA（CPU 节点 1）。绑核在 conv2d.c 内部完成；
# 这里的 OMP 变量只让基准程序自带的参考实现也能用满核，不影响被测函数。
export OMP_NUM_THREADS=38
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_DYNAMIC=FALSE
unset GOMP_CPU_AFFINITY OMP_THREAD_LIMIT 2>/dev/null || true

numactl -N 1 ./conv2d_test 4096 6144 39 39 1
numactl -N 1 ./conv2d_test 6144 4096 41 41 1
numactl -N 1 ./conv2d_test 4256 6390 55 55 1
numactl -N 1 ./conv2d_test 6390 4256 81 81 1
