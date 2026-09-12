#!/usr/bin/env bash
# Historical failed sampling protocol (job 1582107); use v56_k41_sample_job.sh for current profiling.
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
build=build/v56/experiments/k41-profile
result=results/v56/experiments/k41-profile
for v in previous baseline; do
    gcc "${flags[@]}" tools/fbench.c "$build/${v}_phase.c" -o "$build/phase_$v" -lm
    gcc "${flags[@]}" -g tools/profile_driver.c "$build/$v.c" -o "$build/sample_$v" -lm
    objdump -d "$build/sample_$v" > "$result/disas_$v.txt"
done
fifo_dir=$(mktemp -d /tmp/conv-v56-k41-perf.XXXXXX)
trap 'rm -rf "$fifo_dir"' EXIT
mkfifo "$fifo_dir/ctl" "$fifo_dir/ack"
export V54_PERF_CTL="$fifo_dir/ctl" V54_PERF_ACK="$fifo_dir/ack"
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
        echo "SAMPLE memory=$memory variant=$v"
        data="$result/$memory.$v.perf"
        perf record -q -D -1 --control="fifo:$V54_PERF_CTL,$V54_PERF_ACK" -e cycles:u -c 100003 -o "$data" -- "${run[@]}" "$build/sample_$v" 6144 4096 41 41 80
        perf report -i "$data" --stdio --no-children --percent-limit 0.1 > "$result/$memory.$v.report"
        perf annotate -i "$data" --stdio --no-source --symbol=roll_worker > "$result/$memory.$v.annotate"
    done
done
echo "V56_K41_PROFILE_DONE $(date -Is)"
