#!/usr/bin/env bash
# Validate the actual archive through the submission entry point.
set -eo pipefail
cd "$(dirname "$0")/.."
echo "ZIP_ACCEPT_HOST $(hostname) $(date -Is)"
archive="$PWD/submissions/conv.zip"
sha256sum "$archive"
zip_dir=$(mktemp -d /tmp/conv-v52-accept.XXXXXX)
trap 'rm -rf "$zip_dir"' EXIT
unzip -q "$archive" -d "$zip_dir"
sha256sum "$zip_dir/conv/conv2d.c" conv2d.c
cmp "$zip_dir/conv/conv2d.c" conv2d.c
cmp "$zip_dir/conv/bench_conv.c" bench_conv.c
cmp "$zip_dir/conv/run.sh" run.sh
unset OMP_NUM_THREADS OMP_PROC_BIND OMP_PLACES OMP_DYNAMIC GOMP_CPU_AFFINITY
report=$(cd "$zip_dir/conv" && bash run.sh 2>&1)
printf '%s\n' "$report"
passes=$(printf '%s\n' "$report" | awk '/PASS[[:space:]]*$/{n++} END{print n+0}')
[[ "$passes" == 4 && "$report" != *FAIL* ]] || exit 1
source "$(dirname "$0")/v52_setup.sh"
gcc "${flags[@]}" tools/test_pack_reuse.c "$zip_dir/conv/conv2d.c" -o "$zip_dir/reuse_test" -lm -Wl,--wrap=posix_memalign -Wl,--wrap=free
echo ARCHIVE_PACK_REUSE
"${run[@]}" "$zip_dir/reuse_test"
echo "ZIP_ACCEPT_DONE $(date -Is)"
