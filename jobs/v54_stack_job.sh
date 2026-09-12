#!/usr/bin/env bash
# 远端 v54 resumable strip 与本地打包优化的叠加筛选。
# 四方同节点对照：upstream / overlap-only / overlap+kf-neon / kf-neon-only。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
mkdir -p "$S"
for src in upstream candidate; do
    [[ -f "$S/$src.c" ]] || { echo "MISSING $S/$src.c"; exit 1; }
done

gcc "${flags[@]}" tools/fbench.c "$S/upstream.c" -o "$S/fb_upstream" -lm
gcc "${flags[@]}" tools/fbench.c "$S/candidate.c" -o "$S/fb_full" -lm
gcc "${flags[@]}" -DCONV_PACK_KF_NEON=0 tools/fbench.c "$S/candidate.c" -o "$S/fb_overlap" -lm
gcc -O3 -fopenmp tools/test_v54_state.c "$S/candidate.c" -o "$S/state_full" -lm
gcc -O3 -fopenmp -DCONV_PACK_KF_NEON=0 tools/test_v54_state.c "$S/candidate.c" -o "$S/state_overlap" -lm
sha256sum "$S/upstream.c" "$S/candidate.c"

echo "=== STATE default overlap+kf-neon"
TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/state_full"
echo "=== STATE overlap-only"
TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/state_overlap"
echo "=== STATE serial-before-workers"
CONV_PACKSER=2 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/state_full"
echo "=== STATE parallel-pack fallback"
CONV_PACKSER=0 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "$S/state_full"

shapes=(
  "4096 6144 39 39"
  "6144 4096 41 41"
  "4256 6390 55 55"
  "6390 4256 81 81"
)
for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        cmd+=(--preferred="$hbm_node")
    fi
    echo "=== SCREEN memory=$memory"
    for round in 1 2 3; do
        order=(upstream overlap full serial)
        (( round == 2 )) && order=(serial full overlap upstream)
        (( round == 3 )) && order=(overlap upstream serial full)
        for args in "${shapes[@]}"; do
            read -ra shape <<< "$args"
            for variant in "${order[@]}"; do
                case "$variant" in
                    upstream) exe="$S/fb_upstream"; mode=() ;;
                    overlap)  exe="$S/fb_overlap";  mode=() ;;
                    full)     exe="$S/fb_full";     mode=() ;;
                    serial)   exe="$S/fb_full";     mode=(CONV_PACKSER=2) ;;
                esac
                printf "STACK memory=%s round=%d variant=%-8s shape=%s " "$memory" "$round" "$variant" "$args"
                report=$(env "${mode[@]}" "${cmd[@]}" "$exe" "${shape[@]}" 5 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V54_STACK_DONE $(date -Is)"
