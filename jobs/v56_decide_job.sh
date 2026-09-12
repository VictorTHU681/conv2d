#!/usr/bin/env bash
# v54（上游）/ v55（已发布）/ v56（+事件重排+权重）同节点官方口径三方定夺。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
for f in upstream.c v55.c candidate.c; do
    [[ -f "$S/$f" ]] || { echo "MISSING $S/$f"; exit 1; }
done
gcc "${flags[@]}" bench_conv.c "$S/upstream.c" -o "$S/d_up" -lm
gcc "${flags[@]}" bench_conv.c "$S/v55.c" -o "$S/d_v55" -lm
gcc "${flags[@]}" bench_conv.c "$S/candidate.c" -o "$S/d_v56" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$S/candidate.c" -o "$S/d_state" -lm
sha256sum "$S/upstream.c" "$S/v55.c" "$S/candidate.c"

echo "=== STATE v56"
TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/d_state" | tail -1

shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        cmd+=(--preferred="$hbm_node")
    fi
    for round in 1 2 3 4 5; do
        order=(up v55 v56)
        (( round % 3 == 2 )) && order=(v56 up v55)
        (( round % 3 == 0 )) && order=(v55 v56 up)
        for args in "${shapes[@]}"; do
            read -ra shape <<< "$args"
            for variant in "${order[@]}"; do
                echo "DECIDE memory=$memory round=$round variant=$variant shape=$args"
                report=$("${cmd[@]}" "$S/d_$variant" "${shape[@]}" 5)
                printf '%s\n' "$report"
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V56_DECIDE_DONE $(date -Is)"
