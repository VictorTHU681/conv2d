#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
variant=${K5_PACKAGE_VARIANT:?Select exact or triples}
case "$variant" in exact|triples) ;; *) exit 2 ;; esac
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
zip_dir=$(mktemp -d /tmp/conv-post61-archive.XXXXXX)
trap 'rm -rf "$zip_dir"' EXIT
stage=build/post61/k5-copy-fixed/package_$variant
echo "K5_PACKAGE_VARIANT $variant"
for archive in conv conv_nf3 conv_diag; do
    echo "ARCHIVE_BEGIN $archive $(date -Is)"
    sha256sum "$stage/submissions/$archive.zip"
    unzip -q "$stage/submissions/$archive.zip" -d "$zip_dir/$archive"
    dir="$zip_dir/$archive/conv"
    cmp "$dir/bench_conv.c" "$stage/bench_conv.c"
    cmp "$dir/README.md" "$stage/README.md"
    if [[ "$archive" == conv ]]; then cmp "$dir/conv2d.c" "$stage/conv2d.c"; fi
    if [[ "$archive" == conv_diag ]]; then cmp "$dir/run.sh" "$stage/run_diag.sh"; else cmp "$dir/run.sh" "$stage/run.sh"; fi
    sha256sum "$dir/conv2d.c"
    report=$(cd "$dir" && bash run.sh 2>&1)
    printf '%s\n' "$report"
    passes=$(printf '%s\n' "$report" | awk '/PASS[[:space:]]*$/{n++} END{print n+0}')
    [[ "$passes" == 4 && "$report" != *FAIL* ]] || exit 1
    echo "ARCHIVE_PASS $archive"
done
echo "K5_COPY_ZIP_DONE $(date -Is)"
