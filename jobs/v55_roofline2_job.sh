#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
cp tools/v55_roofline.c tools/v55_roofline2.c
gcc "${flags[@]}" tools/v55_roofline2.c -o build/v55/roofline2 -lm
gcc "${flags[@]}" tools/fbench.c build/v55/baseline.c -o build/v55/roof_fb -lm
"${run[@]}" build/v55/roofline2
for args in '4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81'; do
    read -ra shape <<< "$args"
    echo "BASELINE_PLACEMENT ${run[*]} shape=$args"
    "${run[@]}" build/v55/roof_fb "${shape[@]}" 5
done
echo "ROOFLINE_DONE $(date -Is)"
