#!/usr/bin/env bash
# 探测 0xd22 核上可用的 ARMv8/9 通用 PMU 事件（对 1 线程 600x1100 k39 计数），找出非零且合理的事件
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date; grep -m1 "CPU part" /proc/cpuinfo
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp tools/drv.c conv2d.c -o build/drv -lm 2>&1 | grep -iE "error"
export OMP_NUM_THREADS=1 OMP_PROC_BIND=close OMP_PLACES=cores
CMD="numactl -N 1 taskset -c 40 build/drv 600 1100 39 39 2"
probe() { perf stat "$@" $CMD 2>&1 | grep -E "^ +[0-9,<]" | awk '{ n=$1; gsub(",","",n); printf "  %-10s %16s\n", $2, n }'; }
probe -e r11:u -e r08:u -e r23:u -e r24:u -e r3c:u -e r3d:u
probe -e r3e:u -e r3f:u -e r4005:u -e r4006:u -e r4007:u -e r4020:u
probe -e r4021:u -e r4022:u -e r39:u -e r4009:u -e r400a:u -e r400b:u
probe -e r70:u -e r71:u -e r73:u -e r74:u -e r75:u -e r7a:u
probe -e r8002:u -e r8006:u -e r8014:u -e r8018:u -e r8074:u -e r8075:u
probe -e r8076:u -e r8077:u -e r80c0:u -e r80c1:u -e r80c2:u -e r80c3:u
probe -e r03:u -e r04:u -e r16:u -e r17:u -e r05:u -e r34:u
probe -e r6c:u -e r6d:u -e r6e:u -e r6f:u -e r7c:u -e r7d:u
probe -e r4008:u -e r4010:u -e r4011:u -e r4012:u -e r4013:u -e r4014:u
probe -e r0d:u -e r0e:u -e r0f:u -e r10:u -e r12:u -e r21:u
probe -e r22:u -e r25:u -e r26:u -e r27:u -e r28:u -e r29:u
probe -e r2a:u -e r2b:u -e r2c:u -e r2d:u -e r2e:u -e r2f:u
probe -e r30:u -e r31:u -e r32:u -e r33:u -e r35:u -e r36:u
probe -e r37:u -e r38:u -e r3a:u -e r3b:u -e r4000:u -e r4001:u
probe -e r400c:u -e r400d:u -e r400e:u -e r400f:u -e r4015:u -e r4016:u
probe -e r8100:u -e r8108:u -e r8110:u -e r8118:u -e r8120:u -e r8128:u
echo "=== DONE"
