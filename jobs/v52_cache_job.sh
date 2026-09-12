#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v52_setup.sh"
for v in baseline cache; do
    gcc "${flags[@]}" tools/test_pack_reuse.c "build/v52/$v.c" -o "build/v52/reuse_$v" -lm -Wl,--wrap=posix_memalign -Wl,--wrap=free
done
echo BASELINE_EXPECT_ALLOCATION_REGRESSION
if "${run[@]}" build/v52/reuse_baseline; then
    echo 'Expected repeated-allocation regression did not reproduce' >&2
    exit 1
fi
echo FIXED_PACK_REUSE
"${run[@]}" build/v52/reuse_cache
echo "CACHE_DONE $(date -Is)"
