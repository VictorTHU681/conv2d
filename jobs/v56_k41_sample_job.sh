#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
build=build/v56/experiments/k41-profile
result=results/v56/experiments/k41-profile
for v in previous baseline; do
    gcc "${flags[@]}" -g tools/v55_pmu_driver.c "$build/$v.c" -o "$build/steady_$v" -lm
    gcc "${flags[@]}" tools/fbench.c "$build/${v}_phase.c" -o "$build/phase_$v" -lm
done
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for round in 1 2 3; do
        order=(previous baseline); (( round % 2 == 0 )) && order=(baseline previous)
        for v in "${order[@]}"; do
            echo "PHASE memory=$memory round=$round variant=$v shape=6144 4096 41 41"
            CONV_ROLL_DIAG=1 "${run[@]}" "$build/phase_$v" 6144 4096 41 41 5
        done
    done
    for v in previous baseline; do
        echo "UNSAMPLED memory=$memory variant=$v"
        "${run[@]}" "$build/steady_$v" 6144 4096 41 41 200
        echo "LOW_RATE_SAMPLE memory=$memory variant=$v frequency=99"
        data="$result/$memory.$v.lowrate.perf"
        perf record -q -e cycles:u -F 99 -o "$data" -- "${run[@]}" "$build/steady_$v" 6144 4096 41 41 200
        perf report -i "$data" --stdio --no-children --percent-limit 0.1 > "$result/$memory.$v.lowrate.report"
        perf annotate -i "$data" --stdio --no-source --symbol=roll_worker > "$result/$memory.$v.lowrate.annotate"
        objdump -d --disassemble=roll_worker "$build/steady_$v" > "$result/$v.steady.worker.txt"
    done
done
echo "V56_K41_SAMPLE_DONE $(date -Is)"
