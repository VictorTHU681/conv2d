#!/usr/bin/env python3
"""Build isolated archive candidates without replacing current submissions."""
from pathlib import Path
import shutil
import subprocess

root=Path('build/v56/experiments/planar-fix-full')
stage=root/'package'
(stage/'tools').mkdir(parents=True,exist_ok=True)
(stage/'submissions').mkdir(exist_ok=True)
shutil.copyfile(root/'mergedfixed.c',stage/'conv2d.c')
for name in ['bench_conv.c','run.sh','run_diag.sh','tools/mkdiag.py','tools/package_v56.py']:
    shutil.copyfile(name,stage/name)
(stage/'README.md').write_text('''# Local v56 integrated boundary-correction candidate

Combines local K9 register reuse with upstream b9591de packing/copy overlap.
Bounds K8/K9/K4 input copies and removes duplicate concurrent pack writers.
Each call rebuilds coefficients and computes all outputs in FP32.

Original build: gcc -O3 bench_conv.c conv2d.c -o conv2d_test -lm -fopenmp
Original placement: OMP_NUM_THREADS=38 numactl -N 1 ./conv2d_test H W KH KW 5
run.sh retains its existing optional HBM preferred placement; CONV_HBM=0 disables it.
The problem statement does not explicitly authorize that additional placement.

conv.zip is the normal candidate; conv_nf3.zip is a three-chain control.
conv_diag.zip contains call-stage and environment probes, for diagnostics only.
This local candidate is still undergoing formal acceptance and has not been pushed.
The audit does not prove absence of all undefined behavior or concurrent-call safety.
''')
subprocess.run(['python3',str(stage/'tools/package_v56.py')],check=True)
