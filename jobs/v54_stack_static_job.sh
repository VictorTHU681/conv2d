#!/usr/bin/env bash
# 静态片段保持版按组放行：快速筛选后才进入完整官方口径。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/upstream.c" -o "$S/static_upstream" -lm
gcc "${flags[@]}" tools/fbench.c "$S/candidate.c" -o "$S/static_candidate" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$S/candidate.c" -o "$S/static_state" -lm
sha256sum "$S/upstream.c" "$S/candidate.c"

TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/static_state"

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        cmd+=(--preferred="$hbm_node")
    fi
    for round in 1 2 3; do
        order=(upstream overlap serial)
        (( round == 2 )) && order=(serial overlap upstream)
        for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
            read -ra shape <<< "$args"
            for variant in "${order[@]}"; do
                case "$variant" in
                    upstream) mode=(); exe="$S/static_upstream" ;;
                    overlap)  mode=(); exe="$S/static_candidate" ;;
                    serial)   mode=(CONV_PACKSER=2); exe="$S/static_candidate" ;;
                esac
                printf "STATIC memory=%s round=%d variant=%-8s shape=%s " "$memory" "$round" "$variant" "$args"
                report=$(env "${mode[@]}" "${cmd[@]}" "$exe" "${shape[@]}" 5 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V54_STACK_STATIC_DONE $(date -Is)"
