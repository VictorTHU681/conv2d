#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
gcc "${flags[@]}" tools/v55_geometry.c -o build/v55/geometry -lm
"${run[@]}" build/v55/geometry
echo "GEOMETRY_DONE $(date -Is)"
