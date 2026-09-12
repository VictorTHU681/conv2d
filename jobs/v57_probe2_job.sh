#!/usr/bin/env bash
# v57 第二轮：MOVAZ 硬件探测 + prfm 成分分解（位精确变体，正常口径 A/B）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v57
echo "=== MOVAZ probe"
if command -v clang-18 >/dev/null 2>&1; then CL=clang-18; else CL=$(ls /usr/bin/clang* /work_ssd/software/*/bin/clang* 2>/dev/null | head -1 || true); fi
echo "clang: ${CL:-none}"
if [[ -n "${CL:-}" ]] && $CL --target=aarch64-linux-gnu -march=armv9-a+sme2p1 -O2 tools/v57_movaz.c -o "$S/movaz" 2>"$S/movaz.err"; then
    set +e
    "${run[@]}" "$S/movaz"; rc=$?
    set -e
    echo "MOVAZ_RC=$rc"
else
    echo "MOVAZ_COMPILE_FAIL"; cat "$S/movaz.err" 2>/dev/null | head -5
fi

for v in base k4_noprf k9_noprf; do
    gcc "${flags[@]}" tools/fbench.c "$S/$v.c" -o "$S/p2_$v" -lm
done

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; cmd+=(--preferred="$hbm_node"); fi
    for round in 1 2 3; do
        for args in '4096 6144 39 39' '4256 6390 55 55' '6390 4256 81 81'; do
            read -ra shape <<< "$args"
            for v in base k4_noprf k9_noprf; do
                printf "P2 memory=%s round=%d variant=%-9s shape=%s " "$memory" "$round" "$v" "$args"
                report=$(env "${cmd[@]}" "$S/p2_$v" "${shape[@]}" 4 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V57_PROBE2_DONE $(date -Is)"
