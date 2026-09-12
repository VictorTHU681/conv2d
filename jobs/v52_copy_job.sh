#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v52_setup.sh"
for v in copy2 copy4; do
    gcc "${flags[@]}" tools/test_conv.c "build/v52/$v.c" -o "build/v52/test_$v" -lm
    gcc "${flags[@]}" tools/fbench.c "build/v52/$v.c" -o "build/v52/fbench_$v" -lm
    echo "SIGNED_BITWISE $v"
    TEST_SIGNED=1 TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" "build/v52/test_$v" 80 52401
done
gcc "${flags[@]}" tools/fbench.c build/v52/baseline.c -o build/v52/copy_baseline -lm
for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    for round in 1 2 3; do
        order=(baseline copy2 copy4 w16_104 w16_106 w4_115 w4_130)
        if (( round % 2 == 0 )); then order=(w4_130 w4_115 w16_106 w16_104 copy4 copy2 baseline); fi
        for v in "${order[@]}"; do
            echo "MEASURE round=$round variant=$v shape=$args"
            exe=build/v52/copy_baseline
            knobs=()
            case "$v" in
                copy*) exe="build/v52/fbench_$v" ;;
                w16_*) knobs=("CONV_ROLL_W16=${v#w16_}") ;;
                w4_*) knobs=("CONV_ROLL_W4=${v#w4_}") ;;
            esac
            env "${knobs[@]}" "${run[@]}" "$exe" "${shape[@]}" 5
        done
    done
done
echo "COPY_DONE $(date -Is)"
