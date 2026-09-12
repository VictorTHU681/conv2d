#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
(( hbm_node >= 0 )) || { echo 'HBM unavailable for this allocation'; exit 2; }
run=(numactl -N "$cpu_node" --preferred="$hbm_node")
root=build/v56/experiments/planar-fix-full
variants=(baseline upstream mergedfixed mergedfixed_p1 mergedfixed_p2 mergedfixed_p3)
for v in baseline upstream mergedfixed; do
    sha256sum "$root/$v.c" "$root/off_$v"
done
# Six Williams-design rows balance process position and predecessor, including an explicit
# mode-3 copy of the default candidate as an unchanged-program control.
order=(0 1 5 2 4 3)
for round in 0 1 2 3 4 5; do
    for offset in 0 1 2 3 4 5; do
        v=${variants[$(((round+order[offset])%6))]}
        src=$v; knobs=()
        if [[ "$v" == *_p? ]]; then src=mergedfixed; knobs=(CONV_PACKSER="${v: -1}"); fi
        echo "K39_ORDER memory=HBM round=$round variant=$v position=$offset"
        cat "/sys/devices/system/cpu/cpu$first_cpu/cpufreq/scaling_cur_freq" 2>/dev/null || true
        report=$(env "${knobs[@]}" "${run[@]}" "$root/off_$src" 4096 6144 39 39 5)
        printf '%s\n' "$report"
        [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
    done
done
# Runtime-enabled per-kernel/thread timing, after the uninstrumented comparison.
for v in "${variants[@]}"; do
    src=$v; knobs=()
    if [[ "$v" == *_p? ]]; then src=mergedfixed; knobs=(CONV_PACKSER="${v: -1}"); fi
    echo "K39_PROFILE memory=HBM variant=$v"
    env "${knobs[@]}" CONV_ROLL_DIAG=1 CONV_ROLL_DIAG_THR=1 "${run[@]}" "$root/off_$src" 4096 6144 39 39 2
done
echo "K39_ORDER_DONE $(date -Is)"
