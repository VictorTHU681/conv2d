#!/usr/bin/env bash
# Set CONV_ACCEPT_VARIANTS to generated candidates selected by screening.
set -eo pipefail
source "$(dirname "$0")/v52_setup.sh"
variants=(${CONV_ACCEPT_VARIANTS:-baseline cache})
for v in "${variants[@]}"; do
    gcc -O3 -fopenmp bench_conv.c "build/v52/$v.c" -o "build/v52/official_$v" -lm
    gcc "${flags[@]}" tools/test_conv.c "build/v52/$v.c" -o "build/v52/accept_test_$v" -lm
    echo "POSITIVE_BITWISE $v"
    TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" "build/v52/accept_test_$v" 150 52301
    echo "SIGNED_BITWISE $v"
    TEST_SIGNED=1 TEST_BITWISE=1 CONV_ROLL=1 "${run[@]}" "build/v52/accept_test_$v" 150 52302
    echo "HEIGHT_REUSE $v"
    TEST_REUSE_HEIGHT=1 TEST_BITWISE=1 "${run[@]}" "build/v52/accept_test_$v" 0 52303
done
for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    for round in 1 2 3 4 5; do
        order=("${variants[@]}")
        if (( round % 2 == 0 )); then
            order=()
            for (( i=${#variants[@]}-1; i>=0; i-- )); do order+=("${variants[i]}"); done
        fi
        for v in "${order[@]}"; do
            echo "OFFICIAL_ACCEPT round=$round variant=$v shape=$args"
            report=$("${run[@]}" "build/v52/official_$v" "${shape[@]}" 5)
            printf '%s\n' "$report"
            [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
        done
    done
done
echo "ACCEPTANCE_DONE $(date -Is)"
