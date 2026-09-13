#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
root=build/v56/experiments/mixed-throughput
if [[ "${CONV_PROBE_FLAVOR:-predicated}" == indexed ]]; then root+=-indexed; fi
echo "MIXED_FLAVOR ${CONV_PROBE_FLAVOR:-predicated}"
sha256sum "$root/probe.c"
gcc "${flags[@]}" "$root/probe.c" -o "$root/probe" -lm
for nt in 1 38; do
    echo "MIXED_BEGIN threads=$nt $(date -Is)"
    cat "/sys/devices/system/cpu/cpu$first_cpu/cpufreq/scaling_cur_freq" 2>/dev/null || true
    OMP_NUM_THREADS="$nt" "${run[@]}" "$root/probe" 1000000
    cat "/sys/devices/system/cpu/cpu$first_cpu/cpufreq/scaling_cur_freq" 2>/dev/null || true
done
echo "MIXED_PROBE_DONE $(date -Is)"
