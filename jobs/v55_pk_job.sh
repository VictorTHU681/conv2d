#!/usr/bin/env bash
# v55 候选4：并行按组放行打包（CONV_PACKSER=3）vs 主线程按组（默认）vs 纯远端 v54。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/upstream.c" -o "$S/pk_up" -lm
gcc "${flags[@]}" tools/fbench.c "$S/candidate.c" -o "$S/pk_cand" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$S/candidate.c" -o "$S/pk_state" -lm
sha256sum "$S/upstream.c" "$S/candidate.c"

echo "=== STATE default"
TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/pk_state" | tail -1
echo "=== STATE packser3"
CONV_PACKSER=3 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/pk_state" | tail -1
echo "=== STATE packser3 step4"
CONV_PACKSER=3 CONV_ROLL_STEP=4 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/pk_state" | tail -1

shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        cmd+=(--preferred="$hbm_node")
    fi
    for round in 1 2 3; do
        order=(up cand cand3)
        (( round == 2 )) && order=(cand3 cand up)
        (( round == 3 )) && order=(cand up cand3)
        for args in "${shapes[@]}"; do
            read -ra shape <<< "$args"
            for variant in "${order[@]}"; do
                case "$variant" in
                    up)    exe="$S/pk_up";   mode=() ;;
                    cand)  exe="$S/pk_cand"; mode=() ;;
                    cand3) exe="$S/pk_cand"; mode=(CONV_PACKSER=3) ;;
                esac
                printf "PK memory=%s round=%d variant=%-5s shape=%s " "$memory" "$round" "$variant" "$args"
                report=$(env "${mode[@]}" "${cmd[@]}" "$exe" "${shape[@]}" 5 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V55_PK_DONE $(date -Is)"
