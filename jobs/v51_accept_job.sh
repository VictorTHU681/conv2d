#!/usr/bin/env bash
# Combined candidates: screening plus complete official-reference acceptance.
set -eo pipefail
export CONV_VARIANTS='baseline k4tail nopfo_clean combo combo_preload'
source "$(dirname "$0")/v51_job.sh"
echo "ACCEPTANCE_BEGIN $(date -Is)"
for v in combo combo_preload; do
    gcc "${flags[@]}" bench_conv.c "build/v51/$v.c" -o "build/v51/official_$v" -lm
    gcc -O3 bench_conv.c "build/v51/$v.c" -o "build/v51/plain_$v" -lm -fopenmp
    echo "SIGNED_BITWISE $v"
    TEST_SIGNED=1 TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" "build/v51/test_$v" 150 51501
    echo "POSITIVE_BITWISE $v"
    TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" "build/v51/test_$v" 150 51502
    echo "HEIGHT_REUSE $v"
    TEST_REUSE_HEIGHT=1 TEST_BITWISE=1 "${run[@]}" "build/v51/test_$v" 0 51503
done
for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    for round in 1 2 3; do
        order=(baseline combo combo_preload)
        if (( round % 2 == 0 )); then order=(combo_preload combo baseline); fi
        for v in "${order[@]}"; do
            echo "OFFICIAL_ACCEPT round=$round variant=$v shape=$args"
            report=$("${run[@]}" "build/v51/official_$v" "${shape[@]}" 3)
            printf '%s\n' "$report"
            [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
        done
    done
    for v in combo combo_preload; do
        echo "PLAIN_ACCEPT variant=$v shape=$args"
        report=$("${run[@]}" "build/v51/plain_$v" "${shape[@]}" 3)
        printf '%s\n' "$report"
        [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
    done
done
echo "ACCEPTANCE_DONE $(date -Is)"
