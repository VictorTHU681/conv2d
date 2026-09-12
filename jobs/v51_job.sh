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
variants=(${CONV_VARIANTS:-baseline unroll2 unroll4 k4tail offset2 offset4 full})
gcc -O3 -fopenmp tools/quant_audit.c -o build/v51/quant_audit -lm
"${run[@]}" build/v51/quant_audit 256
for v in "${variants[@]}"; do
    gcc "${flags[@]}" tools/test_conv.c "build/v51/$v.c" -o "build/v51/test_$v" -lm
    gcc "${flags[@]}" tools/fbench.c "build/v51/$v.c" -o "build/v51/fbench_$v" -lm
    echo "GENERALIZE $v"
    CONV_ROLL=1 "${run[@]}" "build/v51/test_$v" 40 51201
done
if [[ -f build/v51/heightfix.c ]]; then
    gcc "${flags[@]}" tools/test_conv.c build/v51/heightfix.c -o build/v51/test_heightfix -lm
    echo "HEIGHT_REUSE_BASELINE_EXPECT_FAIL"
    if TEST_REUSE_HEIGHT=1 TEST_BITWISE=1 "${run[@]}" build/v51/test_baseline 0 51301; then
        echo 'Expected baseline height-cache regression was not reproduced' >&2
        exit 1
    fi
    echo "HEIGHT_REUSE_FIXED"
    TEST_REUSE_HEIGHT=1 TEST_BITWISE=1 "${run[@]}" build/v51/test_heightfix 40 51301
    echo "SIGNED_BITWISE_FIXED"
    TEST_SIGNED=1 TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" build/v51/test_heightfix 40 51302
fi
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
echo 'MEMORY_AND_KERNEL_DIAGNOSTICS'
for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    echo "BASELINE_LOCAL_DDR shape=$args"
    numactl -N "$cpu_node" -m "$cpu_node" build/v51/fbench_baseline "${shape[@]}" 3
    echo "BASELINE_KERNEL_PROFILE shape=$args"
    CONV_ROLL_DIAG=1 "${run[@]}" build/v51/fbench_baseline "${shape[@]}" 2
done
echo "DONE $(date -Is)"
