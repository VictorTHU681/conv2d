#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"
gcc "${flags[@]}" -g tools/profile_driver.c build/v54/baseline.c -o build/v54/profile_driver -lm
fifo_dir=$(mktemp -d /tmp/conv-v54-perf.XXXXXX)
trap 'rm -rf "$fifo_dir"' EXIT
mkfifo "$fifo_dir/ctl" "$fifo_dir/ack"
export V54_PERF_CTL="$fifo_dir/ctl" V54_PERF_ACK="$fifo_dir/ack"
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    echo "KERNEL_ONLY_SAMPLE memory=$memory"
    perf record -q -D -1 --control="fifo:$V54_PERF_CTL,$V54_PERF_ACK" -e cycles:u -c 100003 -o "results/v54/$memory.kernel.perf" -- "${run[@]}" build/v54/profile_driver 4096 6144 39 39 50
    perf report -i "results/v54/$memory.kernel.perf" --stdio --no-children --percent-limit 0.1 > "results/v54/$memory.kernel.report"
    perf annotate -i "results/v54/$memory.kernel.perf" --stdio --symbol=roll_worker > "results/v54/$memory.kernel.annotate"
    head -35 "results/v54/$memory.kernel.report"
done
echo "SAMPLE_DONE $(date -Is)"
