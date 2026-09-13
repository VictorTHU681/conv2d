#!/usr/bin/env bash
# Negative control for sub-percent comparisons: all executable bytes identical.
set -eo pipefail
source "$(dirname "$0")/v55_setup.sh"
while IFS= read -r name; do unset "$name"; done < <(compgen -v CONV_)
unset FBENCH_FORCE
source_bin=build/post63/k5-copy-order/bench_baseline
printf '%s\n' 'fedb6ea1d4dfac290a0b3d87476533b38d2bee8bf4654f6748414b554703e83b  build/post63/k5-copy-order/bench_baseline' | sha256sum -c -
root=build/post63/identical-binary
# Unique experiment directory; do not overwrite or re-run an existing control.
[[ ! -e "$root/control0/bench" ]]
mkdir -p "$root/control0" "$root/control1" "$root/control2"
cp "$source_bin" "$root/control0/bench"
ln "$root/control0/bench" "$root/control1/bench"
cp "$root/control0/bench" "$root/control2/bench"
sha256sum "$source_bin"
for v in 0 1 2; do
    sha256sum "$root/control$v/bench"
    stat -c "CONTROL_INODE variant=$v device=%d inode=%i size=%s" "$root/control$v/bench"
done
# Same-length paths, no variant environment knob. Control0/1 share an inode;
# control2 is an independent file with the same contents. This is not a kernel change.
orders=('0 1 2' '1 2 0' '2 0 1' '2 1 0' '0 2 1' '1 0 2')
shapes=('4096 6144 39 39' '6144 4096 41 41' '4256 6390 55 55' '6390 4256 81 81')
for round in 0 1 2 3 4 5; do
    read -ra order <<< "${orders[$round]}"
    for memory in DDR HBM; do
        run=(numactl -N "$cpu_node")
        if [[ "$memory" == HBM ]]; then
            (( hbm_node >= 0 )) || continue
            run+=(--preferred="$hbm_node")
        fi
        for shape in "${shapes[@]}"; do
            read -ra args <<< "$shape"
            for v in "${order[@]}"; do
                echo "IDENTICAL memory=$memory round=$round variant=$v shape=$shape"
                "${run[@]}" "$root/control$v/bench" "${args[@]}" 5
            done
        done
    done
done
echo "IDENTICAL_DONE $(date -Is)"
# Read-only permission probe on this allocated node. Failure is recorded,
# not bypassed; no system configuration or permissions are changed.
echo 'PMU_PROBE_BEGIN'
if command -v perf >/dev/null 2>&1; then
    if "${run[@]}" perf stat -e cycles:u,instructions:u -- true; then
        echo 'PMU_PROBE_AVAILABLE'
    else
        echo "PMU_PROBE_UNAVAILABLE status=$?"
    fi
else
    echo 'PMU_PROBE_NO_PERF'
fi
echo 'PMU_PROBE_END'
