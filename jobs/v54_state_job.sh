#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"
for v in shared256 shared512 foldshared; do
    gcc -O3 -fopenmp tools/test_v54_state.c "build/v54/$v.c" -o "build/v54/state_$v" -lm
    gcc -O3 -fopenmp tools/test_pack_reuse.c "build/v54/$v.c" -o "build/v54/reuse_$v" -lm -Wl,--wrap=posix_memalign -Wl,--wrap=free
    echo "STATE_BEGIN variant=$v plain_compile=yes"
    OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "build/v54/state_$v"
    "${run[@]}" "build/v54/reuse_$v"
done
echo "STATE_DONE $(date -Is)"
