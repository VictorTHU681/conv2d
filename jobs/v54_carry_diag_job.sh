#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"
for args in '4096 6144 39 39' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    for v in baseline carry512 baseline; do
        echo "CARRY_PROFILE variant=$v shape=$args"
        CONV_ROLL_DIAG=1 CONV_ROLL_DIAG_THR=1 "${run[@]}" "build/v54/cfb_$v" "${shape[@]}" 2
        cat "/sys/devices/system/cpu/cpu$first_cpu/cpufreq/scaling_cur_freq"
    done
done
echo "CARRY_DIAG_DONE $(date -Is)"
