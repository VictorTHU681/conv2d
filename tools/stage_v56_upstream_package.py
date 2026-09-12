#!/usr/bin/env python3
"""Stage the upstream-gate integration without replacing accepted archives."""
from pathlib import Path
import shutil
import subprocess
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--experiment',choices=['upstream-gate','kf-share'],default='upstream-gate')
args=parser.parse_args()
root=Path('build/v56/experiments')/args.experiment;stage=root/'package'
(stage/'tools').mkdir(parents=True,exist_ok=True)
(stage/'submissions').mkdir(exist_ok=True)
shutil.copyfile(root/'merged.c',stage/'conv2d.c')
for name in ['bench_conv.c','run.sh','run_diag.sh','tools/mkdiag.py','tools/package_v56.py']:
    shutil.copyfile(name,stage/name)
readme='''# Local v56 upstream F4 gate integration candidate

Integrates upstream 87fa5d7's long-row F4 copy overlap and alignment gate.
Retains local K9 reuse, bounded input copies, unique coefficient-pack writers,
row-chunk output dependencies, and integer warmup output-address arithmetic.
Each call rebuilds coefficients and computes complete FP32 outputs.

Original build: gcc -O3 bench_conv.c conv2d.c -o conv2d_test -lm -fopenmp
Original placement: OMP_NUM_THREADS=38 numactl -N 1 ./conv2d_test H W KH KW 5
run.sh retains optional HBM preferred placement; CONV_HBM=0 disables it.
That extra placement is not explicitly authorized in the saved problem statement.
conv.zip is the normal candidate; conv_nf3.zip is a three-chain control.
conv_diag.zip contains call-stage/environment probes and is diagnostic-only.
This unpublished integration is undergoing acceptance, not yet adopted.
External concurrent callers, allocation failures and other SVL hardware remain
outside the validated scope. K5 experiments are not included.
'''
if args.experiment=='kf-share':
    readme=readme.replace('upstream F4 gate integration candidate','shared folded coefficient tables candidate').replace(
        "Integrates upstream 87fa5d7's long-row F4 copy overlap and alignment gate.",
        "Integrates upstream 76ec03d's within-call sharing of equal folded coefficient tables.\nOnly each table owner writes; consumers wait for its group to publish completion.\nThe accepted F4 gate remains in place; the K9 weight default stays 140.")
(stage/'README.md').write_text(readme)
subprocess.run(['python3',str(stage/'tools/package_v56.py')],check=True)
