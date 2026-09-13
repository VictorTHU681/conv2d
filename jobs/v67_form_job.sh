#!/usr/bin/env bash
# v67 侦察：k41/k81 的 pairf4 满槽形态在本节点是否翻车（对照老形态），k39 NF 差作节点档标定。
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"

S=build/v54_stack
gcc "${flags[@]}" tools/fbench.c "$S/k8ext.c" -o "$S/s_form" -lm
sha256sum "$S/k8ext.c"

for memory in HBM DDR; do
    cmd=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then (( hbm_node >= 0 )) || continue; cmd+=(--preferred="$hbm_node"); fi
    for round in 1 2 3; do
        pairs=('def k5c0 6144 4096 41 41' 'def k9c0 6390 4256 81 81' 'def nf4 4096 6144 39 39')
        for pair in "${pairs[@]}"; do
            read -r v1 v2 H W KH KW <<< "$pair"
            order=("$v1" "$v2"); (( round == 2 )) && order=("$v2" "$v1")
            for v in "${order[@]}"; do
                case "$v" in
                    def)  mode=() ;;
                    k5c0) mode=(CONV_K5CONV=0) ;;
                    k9c0) mode=(CONV_K9CONV=0) ;;
                    nf4)  mode=(CONV_NF=4) ;;
                esac
                printf "FORM memory=%s round=%d variant=%-5s shape=%s %s %s %s " "$memory" "$round" "$v" "$H" "$W" "$KH" "$KW"
                report=$(env "${mode[@]}" "${cmd[@]}" "$S/s_form" "$H" "$W" "$KH" "$KW" 4 2>&1)
                printf '%s\n' "$report" | tail -1
                [[ "$report" == *PASS* && "$report" != *FAIL* ]] || exit 1
            done
        done
    done
done
echo "V67_FORM_DONE $(date -Is)"
