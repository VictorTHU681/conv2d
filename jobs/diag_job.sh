#!/usr/bin/env bash
# 归因诊断（结果错误、只看时间）：a/b 数据 L1 驻留 vs 真实；无 sweep；单线程全尺寸 k39/k81 + 38 线程 k39
cd "$(dirname "$0")/.." || exit 1
echo "=== HOST"; hostname; date
set +u; . /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
F="-O3 -march=armv9-a+sme+sve2 -fopenmp"; mkdir -p build
gcc $F tools/drv.c conv2d.c -o build/drv -lm 2>&1 | grep -iE "error"
gcc $F -DCONV_NOHALF tools/drv.c conv2d.c -o build/drv_nohalf -lm 2>&1 | grep -iE "error"
gcc $F -DCONV_NOPFROW tools/drv.c conv2d.c -o build/drv_nopf -lm 2>&1 | grep -iE "error"
export OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
r1() { echo "## 1T $1"; shift; env "$@" numactl -N 1 taskset -c 40 2>&1 | grep GFLOPS | tail -1; }
export OMP_NUM_THREADS=1
for cs in "4096 6144 39 39 2" "6390 4256 81 81 1"; do
  echo "##### 1 线程 $cs"
  for cfg in "真实:build/drv:X=1" "a L1驻留:build/drv:CONV_DIAG_L1=1" "a+b L1驻留:build/drv:CONV_DIAG_L1=2" "a+b L1 且无行预取:build/drv_nopf:CONV_DIAG_L1=2" "无 sweep:build/drv_nohalf:X=1" "无 sweep + a+b L1:build/drv_nohalf:CONV_DIAG_L1=2" "BR=0:build/drv:CONV_BR=0" "BR=0 + a+b L1:build/drv:CONV_BR=0 CONV_DIAG_L1=2" "a+b L1 无切片无回写:build/drv:CONV_DIAG_L1=2 CONV_SLICE=0 CONV_STORE=0" "a+b L1 无切片无回写无预取:build/drv:CONV_DIAG_L1=2 CONV_SLICE=0 CONV_STORE=0 CONV_PFIN=0 CONV_PFOUT=0"; do
    name=${cfg%%:*}; rest=${cfg#*:}; bin=${rest%%:*}; envs=${rest#*:}
    printf "  %-28s " "$name"; env $envs numactl -N 1 taskset -c 40 $bin $cs 2>&1 | grep GFLOPS | tail -1 | sed -E "s/.*best +([0-9.]+) ms = +([0-9.]+) GFLOPS.*/\1 ms  \2 GFLOPS/"
  done
done
export OMP_NUM_THREADS=38
echo "##### 38 线程 k39"
for cfg in "真实:build/drv:X=1" "a+b L1驻留:build/drv:CONV_DIAG_L1=2" "无 sweep:build/drv_nohalf:X=1"; do
  name=${cfg%%:*}; rest=${cfg#*:}; bin=${rest%%:*}; envs=${rest#*:}
  printf "  %-28s " "$name"; env $envs numactl -N 1 $bin 4096 6144 39 39 5 2>&1 | grep GFLOPS | tail -1 | sed -E "s/.*best +([0-9.]+) ms = +([0-9.]+) GFLOPS.*/\1 ms  \2 GFLOPS/"
done
echo "=== DONE"; date
