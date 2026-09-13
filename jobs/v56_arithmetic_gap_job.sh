#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
# Inherit no convolution tuning or failed-validation timing overrides.
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
root=build/v56/experiments/arithmetic-gap
sha256sum "$root/current.c" "$root/current_profile.c" "$root/fbench.c" "$root/probe.c"
gcc -O3 "$root/fbench.c" "$root/current.c" -o "$root/plain" -lm -fopenmp
gcc -O3 "$root/fbench.c" "$root/current_profile.c" -o "$root/profile" -lm -fopenmp
gcc "${flags[@]}" "$root/probe.c" -o "$root/probe" -lm
sha256sum "$root/plain" "$root/profile" "$root/probe"
shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
calibrate() {
    echo "ARITHMETIC_CALIBRATION round=$1 side=$2 $(date -Is)"
    cat "/sys/devices/system/cpu/cpu$first_cpu/cpufreq/scaling_cur_freq" 2>/dev/null || true
    numactl -N "$cpu_node" "$root/probe" 1000000
}
for round in 0 1 2 3; do
    calibrate "$round" before
    variants=(plain profile)
    if (( round % 2 )); then variants=(profile plain); fi
    for memory in DDR HBM; do
        run=(numactl -N "$cpu_node")
        if [[ "$memory" == HBM ]]; then
            (( hbm_node >= 0 )) || continue
            run+=(--preferred="$hbm_node")
        fi
        for position in 0 1 2 3; do
            index=$(((round+position)%4))
            read -ra shape <<< "${shapes[$index]}"
            for variant in "${variants[@]}"; do
                echo "ARITHMETIC_CONV memory=$memory round=$round variant=$variant shape=${shapes[$index]}"
                if [[ "$variant" == profile ]]; then
                    CONV_ROLL_DIAG=1 "${run[@]}" "$root/profile" "${shape[@]}" 5
                else
                    "${run[@]}" "$root/plain" "${shape[@]}" 5
                fi
            done
        done
    done
    calibrate "$round" after
done
echo "ARITHMETIC_GAP_DONE $(date -Is)"
