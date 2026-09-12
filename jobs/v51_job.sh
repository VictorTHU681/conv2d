#!/usr/bin/env bash
# Reproducible same-node screening. Candidate sources live in build/v51/.
set -eo pipefail
cd "$(dirname "$0")/.."
source /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build/v51 refcache
echo "HOST $(hostname) $(date -Is)"
taskset -pc $$
read -r cpu_node hbm_node < <(python3 - <<'PY'
import os
from pathlib import Path
allowed = os.sched_getaffinity(0)
def cpus(s):
    out = set()
    for part in s.strip().split(','):
        if part:
            a, _, b = part.partition('-')
            out.update(range(int(a), int(b or a) + 1))
    return out
allowed_memory = cpus(next(line.split(':', 1)[1] for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('Mems_allowed_list:')))
nodes = sorted(Path('/sys/devices/system/node').glob('node[0-9]*'), key=lambda p: int(p.name[4:]))
eligible = [p for p in nodes if len(cpus((p/'cpulist').read_text()) & allowed) >= 38]
if not eligible:
    raise SystemExit('No allocated NUMA node with 38 available CPUs')
p = next((p for p in eligible if p.name == 'node1'), eligible[0])
dist = list(map(int, (p/'distance').read_text().split()))
memory = []
for q in nodes:
    if not (q/'cpulist').read_text().strip():
        kb = next(int(l.split()[3]) for l in (q/'meminfo').read_text().splitlines() if 'MemTotal:' in l)
        n = int(q.name[4:])
        if n in allowed_memory and 1048576 <= kb <= 33554432 and dist[n] <= 70:
            memory.append((dist[n], n))
print(int(p.name[4:]), min(memory)[1] if memory else -1)
PY
)
echo "PLACEMENT cpu_node=$cpu_node hbm_node=$hbm_node"
awk '/Cpus_allowed_list|Mems_allowed_list/' /proc/self/status
first_cpu=$(cat "/sys/devices/system/node/node$cpu_node/cpulist" | cut -d- -f1 | cut -d, -f1)
cat "/sys/devices/system/cpu/cpu$first_cpu/cpufreq/scaling_cur_freq" 2>/dev/null || true
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
unset GOMP_CPU_AFFINITY OMP_THREAD_LIMIT
run=(numactl -N "$cpu_node")
if (( hbm_node >= 0 )); then run+=(--preferred="$hbm_node"); fi
flags=(-O3 -march=armv9-a+sme+sve2 -fopenmp)
variants=(${CONV_VARIANTS:-baseline unroll2 unroll4 k4tail})
gcc -O3 -fopenmp tools/quant_audit.c -o build/v51/quant_audit -lm
"${run[@]}" build/v51/quant_audit 256
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/test_conv.c "build/v51/$v.c" -o "build/v51/test_$v" -lm
    gcc "${flags[@]}" tools/fbench.c "build/v51/$v.c" -o "build/v51/fbench_$v" -lm
    echo "GENERALIZE $v"
    CONV_ROLL=1 "${run[@]}" "build/v51/test_$v" 40 51201
done
gcc "${flags[@]}" bench_conv.c build/v51/baseline.c -o build/v51/official_baseline -lm
for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    echo "OFFICIAL_BASELINE $args"
    "${run[@]}" build/v51/official_baseline "${shape[@]}" 3
    for round in 1 2 3; do
        # Reverse alternate rounds to expose drift.
        order=("${variants[@]}")
        if (( round % 2 == 0 )); then
            order=()
            for (( i=${#variants[@]}-1; i>=0; i-- )); do order+=("${variants[i]}"); done
        fi
        for v in "${order[@]}"; do
            echo "MEASURE round=$round variant=$v shape=$args"
            "${run[@]}" "build/v51/fbench_$v" "${shape[@]}" 5
        done
    done
done
echo "DONE $(date -Is)"
