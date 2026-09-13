#!/usr/bin/env bash
# v67 侦察：v66 形态下重扫输入预取距离 PD（默认 3）与打包模式 PACKSER（默认 -1=按组重叠）。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/s_env" -lm
sha256sum "$S/k8ext.c"

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; cmd+=(--preferred="$hbm_node"); fi
    for round in 1 2 3; do
        vs=(def pd2 pd4 ps0)
        (( round == 2 )) && vs=(ps0 pd4 pd2 def)
        (( round == 3 )) && vs=(pd4 def ps0 pd2)
        for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
            read -ra shape <<< "$args"
            for v in "${vs[@]}"; do
                case "$v" in
                    def) mode=() ;;
                    pd2) mode=(CONV_ROLL_PD=2) ;;
                    pd4) mode=(CONV_ROLL_PD=4) ;;
                    ps0) mode=(CONV_PACKSER=0) ;;
                esac
                printf "ENV memory=%s round=%d variant=%-4s shape=%s " "$memory" "$round" "$v" "$args"
                report=$(env "${mode[@]}" "${cmd[@]}" "$S/s_env" "${shape[@]}" 3 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V67_ENV_DONE $(date -Is)"
