#!/usr/bin/env python3
"""Freeze accepted convolution and register-only calibration in one experiment."""
from pathlib import Path
import hashlib
import subprocess

root = Path('build/v56/experiments/arithmetic-gap')
subprocess.run(['python3', 'tools/stage_v56_prefetch.py', '--root', str(root)], check=True)
subprocess.run(['python3', 'tools/gen_v56_k5_profile.py', '--root', str(root),
                '--variants', 'current', '--thread-detail', '--table-counts'], check=True)
subprocess.run(['python3', 'tools/gen_v56_mixed_probe.py', '--indexed'], check=True)
probe = Path('build/v56/experiments/mixed-throughput-indexed/probe.c').read_bytes()
assert hashlib.sha256(probe).hexdigest() == 'd52eab79863a34188eb217599a27d78a5562f72c36a0195c567b929c8d210a66'
(root / 'probe.c').write_bytes(probe)
dest = Path('results/v56/experiments/arithmetic-gap')
dest.mkdir(parents=True, exist_ok=True)
manifest = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n'
                   for p in sorted(root.glob('*.c')))
(dest / 'sources.sha256').write_text(manifest)
print(manifest, end='')
