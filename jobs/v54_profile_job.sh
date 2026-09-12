#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"
gcc "${flags[@]}" -g tools/drv.c build/v54/baseline.c -o build/v54/drv -lm
gcc "${flags[@]}" -g tools/fbench.c build/v54/baseline.c -o build/v54/fbench -lm
mkdir -p results/v54
echo PROFILE_INPUT
cat /sys/kernel/mm/transparent_hugepage/enabled
grep -E 'Node +1,' /proc/buddyinfo || true
perf --version
perf list 2>/dev/null | head -60 || true
for memory in DDR HBM; do
    run=(numactl -N "$cpu_node")
    if [[ "$memory" == HBM ]]; then
        (( hbm_node >= 0 )) || continue
        run+=(--preferred="$hbm_node")
    fi
    for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
        read -ra shape <<< "$args"
        echo "PROFILE memory=$memory shape=$args"
        CONV_ROLL_DIAG=1 "${run[@]}" build/v54/fbench "${shape[@]}" 3
        for serial in 0 1; do
            echo "PACK_CONTROL memory=$memory serial=$serial shape=$args"
            CONV_PACKSER=$serial "${run[@]}" build/v54/fbench "${shape[@]}" 3
        done
        echo "PMU memory=$memory shape=$args"
        perf stat -e cycles:u,instructions:u,r03:u,r04:u,r05:u,r34:u -- "${run[@]}" build/v54/drv "${shape[@]}" 80 || echo PMU_UNAVAILABLE
    done
    echo "SAMPLE memory=$memory"
    if perf record -q -e cycles:u -c 100003 -o "results/v54/$memory.perf" -- "${run[@]}" build/v54/drv 4096 6144 39 39 150; then
        perf report -i "results/v54/$memory.perf" --stdio --no-children --percent-limit 0.5 > "results/v54/$memory.report"
        perf annotate -i "results/v54/$memory.perf" --stdio --symbol=k16pairf4 > "results/v54/$memory.annotate" || true
        head -35 "results/v54/$memory.report"
    else
        echo PERF_RECORD_UNAVAILABLE
    fi
done
echo "PROFILE_DONE $(date -Is)"
