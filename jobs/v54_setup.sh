#!/usr/bin/env bash
# Reproducible same-node screening. Candidate sources live in build/v54/.
set -eo pipefail
cd "$(dirname "$0")/.."
source /work_ssd/software/HPCKit/26.1.RC1/setvars.sh --use-gcc >/dev/null 2>&1
mkdir -p build/v54 refcache
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
preferred = 'node' + os.environ.get('CONV_TEST_NODE', '1')
ordered = sorted(nodes, key=lambda p: p.name != preferred)
p = None
for candidate in ordered:
    requested = cpus((candidate/'cpulist').read_text())
    if len(requested) < 38:
        continue
    try:
        # Initial shell affinity can be a service-core mask. Probe the actual
        # kernel-enforced cpuset in this child; numactl does the same for tests.
        os.sched_setaffinity(0, requested)
    except OSError:
        continue
    if len(os.sched_getaffinity(0) & requested) >= 38:
        p = candidate
        break
if p is None:
    raise SystemExit('No permitted NUMA node with 38 available CPUs')
dist = list(map(int, (p/'distance').read_text().split()))
memory = []
for q in nodes:
    if not (q/'cpulist').read_text().strip():
        kb = next(int(l.split()[3]) for l in (q/'meminfo').read_text().splitlines() if 'MemTotal:' in l)
        n = int(q.name[4:])
        if os.environ.get('CONV_USE_HBM', '1') != '0' and n in allowed_memory and 1048576 <= kb <= 33554432 and dist[n] <= 70:
            memory.append((dist[n], n))
print(int(p.name[4:]), min(memory)[1] if memory else -1)
PY
)
echo "PLACEMENT cpu_node=$cpu_node hbm_node=$hbm_node"
awk '/Cpus_allowed_list|Mems_allowed_list/' /proc/self/status
first_cpu=$(cat "/sys/devices/system/node/node$cpu_node/cpulist" | cut -d- -f1 | cut -d, -f1)
cat "/sys/devices/system/cpu/cpu$first_cpu/cpufreq/scaling_cur_freq" 2>/dev/null || true
numactl --show
export OMP_NUM_THREADS=38 OMP_PROC_BIND=close OMP_PLACES=cores OMP_DYNAMIC=FALSE
unset GOMP_CPU_AFFINITY OMP_THREAD_LIMIT
run=(numactl -N "$cpu_node")
if (( hbm_node >= 0 )); then run+=(--preferred="$hbm_node"); fi
echo 'EFFECTIVE_PLACEMENT'
"${run[@]}" numactl --show
flags=(-O3 -march=armv9-a+sme+sve2 -fopenmp)
