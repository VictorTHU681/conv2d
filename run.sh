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

# 环境诊断（仅打印，供回看评测机日志；全部容错）
d() { echo "[run-diag] $*"; }
d "host $(hostname 2>/dev/null) | kernel $(uname -r 2>/dev/null) | $(date '+%F %T' 2>/dev/null) | gcc $(gcc -dumpversion 2>/dev/null)"
d "nproc $(nproc 2>/dev/null) | online $(cat /sys/devices/system/cpu/online 2>/dev/null) | $(grep -m1 'CPU implementer' /proc/cpuinfo 2>/dev/null | tr -s ' ') | $(grep -m1 'CPU part' /proc/cpuinfo 2>/dev/null | tr -s ' ') | $(grep -m1 'CPU variant' /proc/cpuinfo 2>/dev/null | tr -s ' ')"
lscpu 2>/dev/null | grep -E "Model name|Thread\(s\)|Core\(s\)|Socket|NUMA node|L1d|L1i|L2|L3|MHz" | sed 's/  */ /g' | while read -r l; do d "lscpu: $l"; done
numactl -H 2>/dev/null | grep -E "^available|^node 1 cpus|^node 1 size|^node 1 free" | while read -r l; do d "numa: $l"; done
c1=$(numactl -H 2>/dev/null | grep '^node 1 cpus' | awk '{print $4}'); c1=${c1:-0}
for c in $c1 $((c1 + 1)); do
    b=/sys/devices/system/cpu/cpu$c/cpufreq
    d "cpu$c cpufreq: gov $(cat $b/scaling_governor 2>/dev/null) | cur $(cat $b/scaling_cur_freq 2>/dev/null) | hw_cur $(cat $b/cpuinfo_cur_freq 2>/dev/null) | min $(cat $b/cpuinfo_min_freq 2>/dev/null) | max $(cat $b/cpuinfo_max_freq 2>/dev/null) | setspeed $(cat $b/scaling_setspeed 2>/dev/null) | avail $(cat $b/scaling_available_frequencies 2>/dev/null) | drv $(cat $b/scaling_driver 2>/dev/null) | boost $(cat /sys/devices/system/cpu/cpufreq/boost 2>/dev/null)"
done
d "cache cpu$c1: $(for i in 0 1 2 3; do b=/sys/devices/system/cpu/cpu$c1/cache/index$i; [ -d $b ] && printf '%s%s=%s ' "$(cat $b/level 2>/dev/null)" "$(cat $b/type 2>/dev/null | cut -c1)" "$(cat $b/size 2>/dev/null)"; done)"
d "thp $(cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null) | perf_paranoid $(cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null) | product $(cat /sys/devices/virtual/dmi/id/product_name 2>/dev/null) | bios $(cat /sys/devices/virtual/dmi/id/bios_version 2>/dev/null)"
d "mem: $(grep -E 'MemTotal|MemFree|HugePages_Total|Hugepagesize' /proc/meminfo 2>/dev/null | tr -s ' ' | tr '\n' ';')"
d "load: $(cat /proc/loadavg 2>/dev/null) | uptime $(awk '{print int($1/3600)"h"}' /proc/uptime 2>/dev/null)"
d "thermal: $(for t in /sys/class/thermal/thermal_zone*; do [ -d $t ] && printf '%s=%s ' "$(cat $t/type 2>/dev/null)" "$(cat $t/temp 2>/dev/null)"; done 2>/dev/null | cut -c1-200)"
d "cppc cpu$c1: $(for f in highest_perf nominal_perf lowest_perf reference_perf nominal_freq lowest_freq; do printf '%s=%s ' $f "$(cat /sys/devices/system/cpu/cpu$c1/acpi_cppc/$f 2>/dev/null)"; done)"

# 判题口径：38 线程、单一 NUMA（CPU 节点 1）。绑核在 conv2d.c 内部完成；
# 这里的 OMP 变量只让基准程序自带的参考实现也能用满核，不影响被测函数。
export OMP_NUM_THREADS=38
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_DYNAMIC=FALSE
unset GOMP_CPU_AFFINITY OMP_THREAD_LIMIT 2>/dev/null || true

for args in "4096 6144 39 39 1" "6144 4096 41 41 1" "4256 6390 55 55 1" "6390 4256 81 81 1"; do
    d "case $args start $(date '+%T.%N' 2>/dev/null | cut -c1-12) | cpu$c1 cur $(cat /sys/devices/system/cpu/cpu$c1/cpufreq/scaling_cur_freq 2>/dev/null) | load $(cut -d' ' -f1 /proc/loadavg 2>/dev/null)"
    numactl -N 1 ./conv2d_test $args
done
