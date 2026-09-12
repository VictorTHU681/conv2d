#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
for v in local upstream; do
    src="build/v56/experiments/planar-audit/$v.c"
    exe="build/v56/experiments/planar-audit/audit_$v"
    sha256sum "$src"
    gcc -O3 tools/test_v56_planar_audit.c "$src" -o "$exe" -lm -fopenmp
    echo "PLANAR_AUDIT_BEGIN $v"
    AUDIT_EXPECT_OVERREAD=1 OMP_NUM_THREADS=7 "${run[@]}" "$exe"
done
echo "V56_PLANAR_AUDIT_DONE $(date -Is)"
