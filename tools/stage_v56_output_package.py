#!/usr/bin/env python3
"""Package the output-order candidate separately from the accepted archives."""
from pathlib import Path
import shutil
import subprocess
import sys

root=Path('build/v56/experiments/output-order')
pipeline='--pipeline' in sys.argv
stage=root/('pipeline-package' if pipeline else 'package')
(stage/'tools').mkdir(parents=True,exist_ok=True)
(stage/'submissions').mkdir(exist_ok=True)
shutil.copyfile(root/('pipelined.c' if pipeline else 'ordered.c'),stage/'conv2d.c')
for name in ['bench_conv.c','run.sh','run_diag.sh','tools/mkdiag.py','tools/package_v56.py']:
    shutil.copyfile(name,stage/name)
(stage/'README.md').write_text('''# Local v56 output-order correction candidate

Adds acquire/release dependencies between overlapping final-strip row pieces.
Keeps FP32 kernels and accumulation order; rebuilds coefficients each call.
Represents the warmup output cursor as an integer address, avoiding a C pointer
formed before the output array. Retains earlier K8/K9/K4 input-copy fixes.

Original build: gcc -O3 bench_conv.c conv2d.c -o conv2d_test -lm -fopenmp
Original placement: OMP_NUM_THREADS=38 numactl -N 1 ./conv2d_test H W KH KW 5
run.sh retains optional HBM preferred placement; CONV_HBM=0 disables it.
The problem statement does not explicitly authorize the additional placement.
conv.zip is the normal candidate; conv_nf3.zip is a three-chain control.
conv_diag.zip contains call-stage/environment probes, for diagnostics only.
This unpublished candidate is undergoing acceptance. The audit does not prove
absence of all undefined behavior or safety of simultaneous external callers.
''')
if pipeline:
    with (stage/'README.md').open('a') as f:
        f.write('\nThis candidate waits for the overlapping output rows of each chunk,\n'
                'rather than waiting for an entire predecessor piece to finish.\n')
subprocess.run(['python3',str(stage/'tools/package_v56.py')],check=True)
