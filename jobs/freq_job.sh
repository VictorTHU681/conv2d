#!/usr/bin/env bash
# 只读检查：计算节点 cpufreq 是否可由用户改动（频率是 fmopa 形态唯一能突破 13.0/13.1 上限的杠杆）
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; id
D=/sys/devices/system/cpu/cpu40/cpufreq
echo "=== ls -l $D"; ls -l $D 2>&1
for f in scaling_governor scaling_cur_freq cpuinfo_cur_freq scaling_min_freq scaling_max_freq cpuinfo_min_freq cpuinfo_max_freq \
         scaling_available_frequencies scaling_available_governors scaling_driver scaling_setspeed related_cpus affected_cpus; do
  printf "%-32s " "$f"; cat $D/$f 2>&1 | head -1
done
echo "=== writable?"; for f in scaling_setspeed scaling_governor scaling_max_freq scaling_min_freq; do
  if [ -w $D/$f ]; then echo "$f: WRITABLE"; else echo "$f: not writable"; fi; done
echo "=== policies"; ls /sys/devices/system/cpu/cpufreq/ 2>&1 | head; 
echo "=== boost"; cat /sys/devices/system/cpu/cpufreq/boost 2>&1
echo "=== tools"; which cpupower cpufreq-set cpufreq-info 2>&1; sudo -n -l 2>&1 | head -5
echo "=== per-cpu cur freq (node1 cpus)"; for c in $(numactl -H | awk '/node 1 cpus/{for(i=4;i<=NF;i++)print $i}'); do cat /sys/devices/system/cpu/cpu$c/cpufreq/scaling_cur_freq 2>/dev/null; done | sort | uniq -c
echo "=== lscpu"; lscpu | grep -iE "model name|mhz|thread|core|socket|numa|l1d|l2|l3"
echo "=== cpuinfo"; grep -m1 -iE "cpu mhz|bogomips" /proc/cpuinfo
echo "=== measured clock under load"; set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
(cd probe && gcc -O2 -march=armv9-a+sme+sve2 smef32.c -o smef32 2>&1 | grep -iE "error")
taskset -c 40 ./probe/smef32 0 | tail -2
echo "=== DONE"; date
