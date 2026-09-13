#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
sha256sum -c results/post64/package-check/archives.sha256
zip_dir=$(mktemp -d /tmp/conv-post64-package.XXXXXX)
trap 'rm -rf "$zip_dir"' EXIT
for variant in upstream aligned; do
    stage=build/post64/package-check/$variant
    for archive in conv conv_nf3 conv_diag; do
        echo "ARCHIVE_BEGIN variant=$variant archive=$archive $(date -Is)"
        sha256sum "$stage/submissions/$archive.zip"
        unzip -q "$stage/submissions/$archive.zip" -d "$zip_dir/$variant/$archive"
        dir="$zip_dir/$variant/$archive/conv"
        cmp "$dir/bench_conv.c" "$stage/bench_conv.c"
        cmp "$dir/README.md" "$stage/README.md"
        if [[ "$archive" == conv ]]; then cmp "$dir/conv2d.c" "$stage/conv2d.c"; fi
        if [[ "$archive" == conv_diag ]]; then cmp "$dir/run.sh" "$stage/run_diag.sh"; else cmp "$dir/run.sh" "$stage/run.sh"; fi
        sha256sum "$dir/conv2d.c"
        report=$(cd "$dir" && bash run.sh 2>&1)
        printf '%s\n' "$report"
        passes=$(printf '%s\n' "$report" | awk '/PASS[[:space:]]*$/{n++} END{print n+0}')
        [[ "$passes" == 4 && "$report" != *FAIL* ]] || exit 1
        echo "ARCHIVE_PASS variant=$variant archive=$archive"
    done
done
echo "POST64_PACKAGES_DONE $(date -Is)"
