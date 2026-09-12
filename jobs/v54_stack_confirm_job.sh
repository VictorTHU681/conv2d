#!/usr/bin/env bash
# 远端 v54 与最小叠加版（仅每调用按组打包/放行）的正式口径确认。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
for src in upstream.c candidate.c; do
    [[ -f "$S/$src" ]] || { echo "MISSING $S/$src"; exit 1; }
done

gcc "${flags[@]}" bench_conv.c "$S/upstream.c" -o "$S/off_upstream" -lm
gcc "${flags[@]}" bench_conv.c "$S/candidate.c" -o "$S/off_overlap" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$S/candidate.c" -o "$S/state_overlap_final" -lm
gcc -O3 -fopenmp bench_conv.c "$S/candidate.c" -o "$S/off_overlap_plain" -lm
sha256sum "$S/upstream.c" "$S/candidate.c"

echo "=== FINAL_STATE"
TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/state_overlap_final"
echo "=== PLAIN_COMPILE_OFFICIAL"
for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    report=$("${run[@]}" "$S/off_overlap_plain" "${shape[@]}" 1)
    printf '%s\n' "$report"
    [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
done

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        cmd+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        for round in 1 2 3 4 5; do
            order=(upstream overlap serial)
            (( round % 2 == 0 )) && order=(serial overlap upstream)
            for variant in "${order[@]}"; do
                case "$variant" in
                    upstream) mode=(); exe="$S/off_upstream" ;;
                    overlap)  mode=(); exe="$S/off_overlap" ;;
                    serial)   mode=(CONV_PACKSER=2); exe="$S/off_overlap" ;;
                esac
                echo "STACK_FINAL memory=$memory round=$round variant=$variant shape=$args"
                report=$(env "${mode[@]}" "${cmd[@]}" "$exe" "${shape[@]}" 5)
                printf '%s\n' "$report"
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V54_STACK_CONFIRM_DONE $(date -Is)"
