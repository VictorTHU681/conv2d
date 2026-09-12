#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
zip_dir=$(mktemp -d /tmp/conv-v55-archive.XXXXXX)
trap 'rm -rf "$zip_dir"' EXIT
for archive in conv conv_nf3 conv_diag; do
    echo "ARCHIVE_BEGIN $archive $(date -Is)"
    sha256sum "submissions/$archive.zip"
    unzip -q "submissions/$archive.zip" -d "$zip_dir/$archive"
    dir="$zip_dir/$archive/conv"
    cmp "$dir/bench_conv.c" bench_conv.c
    cmp "$dir/README.md" README.md
    if [[ "$archive" == conv ]]; then cmp "$dir/conv2d.c" conv2d.c; fi
    if [[ "$archive" == conv_diag ]]; then cmp "$dir/run.sh" run_diag.sh; else cmp "$dir/run.sh" run.sh; fi
    sha256sum "$dir/conv2d.c"
    report=$(cd "$dir" && bash run.sh 2>&1)
    printf '%s\n' "$report"
    passes=$(printf '%s\n' "$report" | awk '/PASS[[:space:]]*$/{n++} END{print n+0}')
    [[ "$passes" == 4 && "$report" != *FAIL* ]] || exit 1
    echo "ARCHIVE_PASS $archive"
done
echo "ZIP_DONE $(date -Is)"
