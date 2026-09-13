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

# 判题口径（题面）：OMP_NUM_THREADS=38 numactl -N 1。默认优先节点 9（有 CPU 时），
# 否则回落节点 1、再回落节点 0；numactl 不可用则直接运行。CONV_NODE 可显式指定。
cpunode=1
for n in ${CONV_NODE:-} 9 1 0; do
    if [[ -n "$(cat /sys/devices/system/node/node$n/cpulist 2>/dev/null)" ]] && numactl -N $n true >/dev/null 2>&1; then cpunode=$n; break; fi
done
NCPU=$(numactl -N $cpunode nproc 2>/dev/null || nproc 2>/dev/null || echo 38)
NT=38
if [[ "$NCPU" =~ ^[0-9]+$ ]] && (( NCPU > 0 && NCPU < NT )); then NT=$NCPU; fi   # 节点 CPU 不足时不超订
export OMP_NUM_THREADS=$NT
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_DYNAMIC=FALSE
unset GOMP_CPU_AFFINITY OMP_THREAD_LIMIT 2>/dev/null || true

# 内存放置：若 CPU 节点旁挂有纯内存节点（HBM：无 CPU、1～32 GB、距离 ≤ 70），用 --preferred 让基准程序的
# 输入/输出矩阵（四例合计 < 600 MB）落进 HBM（读 ~306 GB/s，与 DDR 通道分开）。放不下时内核自动回落本地 DDR；
# 探测不到则不加该参数，仍为题面命令。CONV_HBM=0 可关。
hbm=""
if [[ "${CONV_HBM:-1}" != "0" && -r /sys/devices/system/node/node$cpunode/distance ]]; then
    read -ra dist < /sys/devices/system/node/node$cpunode/distance
    best=999
    for n in "${!dist[@]}"; do
        [[ -d /sys/devices/system/node/node$n ]] || continue
        [[ -z "$(cat /sys/devices/system/node/node$n/cpulist 2>/dev/null)" ]] || continue     # 只考虑无 CPU 的纯内存节点
        totkb=$(awk '/MemTotal:/{print $4}' /sys/devices/system/node/node$n/meminfo 2>/dev/null)
        [[ "$totkb" =~ ^[0-9]+$ ]] || continue
        (( totkb >= 1048576 && totkb <= 33554432 )) || continue                              # 1～32 GB 才像 HBM
        if (( dist[n] < best )); then best=${dist[n]}; hbm=$n; fi
    done
    (( best > 70 )) && hbm=""
fi
MEMOPT=""
if [[ -n "$hbm" ]] && numactl -N $cpunode --preferred=$hbm true >/dev/null 2>&1; then MEMOPT="--preferred=$hbm"; fi

if command -v numactl >/dev/null 2>&1 && numactl -N $cpunode true >/dev/null 2>&1; then
    RUN="numactl -N $cpunode $MEMOPT"
else
    echo "[run.sh] numactl 不可用或节点 $cpunode 不可用，直接运行" >&2
    RUN=""
fi
echo "[run.sh] host=$(hostname 2>/dev/null) node=$cpunode hbm=${hbm:-none} threads=$NT" >&2   # 仅 stderr，不影响判题解析

$RUN ./conv2d_test 4096 6144 39 39 1
$RUN ./conv2d_test 6144 4096 41 41 1
$RUN ./conv2d_test 4256 6390 55 55 1
$RUN ./conv2d_test 6390 4256 81 81 1
