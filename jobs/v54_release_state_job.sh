#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v54_setup.sh"
for v in release; do
    gcc -O3 -fopenmp tools/test_v54_state.c "build/v54/$v.c" -o "build/v54/state_$v" -lm
    gcc -O3 -fopenmp tools/test_pack_reuse.c "build/v54/$v.c" -o "build/v54/reuse_$v" -lm -Wl,--wrap=posix_memalign -Wl,--wrap=free
    echo "STATE_BEGIN variant=$v plain_compile=yes"
    OMP_NUM_THREADS=7 TEST_BITWISE=1 TEST_SIGNED=1 "${run[@]}" "build/v54/state_$v"
    "${run[@]}" "build/v54/reuse_$v"
    gcc -O3 -fopenmp tools/test_conv.c "build/v54/$v.c" -o "build/v54/release_general" -lm
    for setting in default classic fallback; do
        echo "RELEASE_PATH $setting"
        mode=(); [[ "$setting" == classic ]] && mode=(CONV_ROLL=0)
        [[ "$setting" == fallback ]] && mode=(CONV_NO_SME=1)
        env "${mode[@]}" TEST_BITWISE=1 TEST_SIGNED=1 TEST_REUSE_HEIGHT=1 "${run[@]}" build/v54/release_general 80 55901
    done
done
echo "RELEASE_STATE_DONE $(date -Is)"
