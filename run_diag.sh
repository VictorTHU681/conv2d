#!/usr/bin/env bash
# CONV 赛题·诊断构建：编译(-DCONV_DIAG_ONLINE) + 四组测试用例。
# stdout 额外输出 [run-diag]（机器状态）与 [conv-diag]（每次调用的线程时长/主频/fmopa/带宽/内核周期），用于排查线上不稳定。
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

echo "[run-diag] host=$(hostname 2>/dev/null) kernel=$(uname -r 2>/dev/null) date=$(date '+%F %T') gcc=$(gcc -dumpversion 2>/dev/null)"
echo "[run-diag] loadavg=$(cat /proc/loadavg 2>/dev/null)"
lscpu 2>/dev/null | grep -E "^CPU\(s\)|Model name|NUMA node\(s\)" | sed 's/^/[run-diag] /'
echo "[run-diag] thp=$(cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null)"
grep -E "MemFree|AnonHugePages" /proc/meminfo 2>/dev/null | tr -s ' ' | sed 's/^/[run-diag] /'

rm -f conv2d_test
if ! gcc -O3 -march=armv9-a+sme+sve2 -DCONV_DIAG_ONLINE -fopenmp bench_conv.c conv2d.c -o conv2d_test -lm 2>/dev/null; then
    echo "[run.sh] 编译器不支持 SME 扩展，回退通用实现" >&2
    if ! gcc -O3 -march=armv8.2-a+sve -fopenmp -DCONV_NO_SME_ASM -DCONV_DIAG_ONLINE bench_conv.c conv2d.c -o conv2d_test -lm 2>/dev/null; then
        gcc -O3 -fopenmp -DCONV_NO_SME_ASM -DCONV_DIAG_ONLINE bench_conv.c conv2d.c -o conv2d_test -lm
    fi
fi

# 判题口径（题面）：OMP_NUM_THREADS=38 numactl -N 1。节点 1 无 CPU 时回落节点 0；numactl 不可用则直接运行。
cpunode=1
for n in 1 0; do
    if [[ -n "$(cat /sys/devices/system/node/node$n/cpulist 2>/dev/null)" ]] && numactl -N $n true >/dev/null 2>&1; then cpunode=$n; break; fi
done
NCPU=$(numactl -N $cpunode nproc 2>/dev/null || nproc 2>/dev/null || echo 38)
NT=38
if [[ "$NCPU" =~ ^[0-9]+$ ]] && (( NCPU > 0 && NCPU < NT )); then NT=$NCPU; fi
export OMP_NUM_THREADS=$NT
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_DYNAMIC=FALSE
unset GOMP_CPU_AFFINITY OMP_THREAD_LIMIT 2>/dev/null || true

if command -v numactl >/dev/null 2>&1 && numactl -N $cpunode true >/dev/null 2>&1; then
    RUN="numactl -N $cpunode"
else
    echo "[run.sh] numactl 不可用或节点 $cpunode 不可用，直接运行" >&2
    RUN=""
fi
FIRSTCPU=$(sed 's/[-,].*//' /sys/devices/system/node/node$cpunode/cpulist 2>/dev/null)
echo "[run-diag] node=$cpunode threads=$NT firstcpu=${FIRSTCPU:-?} numa_free=$(numactl -H 2>/dev/null | grep "node $cpunode free" | tr -s ' ')"

for args in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do
    echo "[run-diag] case '$args' start=$(date '+%T') loadavg=$(cut -d' ' -f1-3 /proc/loadavg 2>/dev/null) freq_kHz=$(cat /sys/devices/system/cpu/cpu${FIRSTCPU:-0}/cpufreq/scaling_cur_freq 2>/dev/null)"
    $RUN ./conv2d_test $args
done
echo "[run-diag] all done $(date '+%T') loadavg=$(cut -d' ' -f1-3 /proc/loadavg 2>/dev/null)"
