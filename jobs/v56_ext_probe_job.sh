#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/ext-throughput
sha256sum "$root/probe.c"
gcc "${flags[@]}" "$root/probe.c" -o "$root/probe" -lm
objdump -d "$root/probe" > "$root/disassembly.txt"
for nt in 1 38; do
    echo "EXT_BEGIN threads=$nt $(date -Is)"
    cat "/sys/devices/system/cpu/cpu$first_cpu/cpufreq/scaling_cur_freq" 2>/dev/null || true
    OMP_NUM_THREADS="$nt" "${run[@]}" "$root/probe" 1000000
done
echo "EXT_PROBE_DONE $(date -Is)"
