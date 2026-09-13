#!/usr/bin/env python3
"""Build isolated indexed-store K4 archives with pinned upstream packaging tools."""
from pathlib import Path
import hashlib,subprocess,zipfile
root=Path('build/post64/k4-indexed-packages');out=Path('results/post64/k4-indexed-packages')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
source=Path('build/post64/k4-indexed-store/all.c').read_bytes()
assert hashlib.sha256(source).hexdigest()=='d56e8e9b9b427cf1f1b1f91c40f19ffb0e88ce18b52a03d5be0878b3bce9fa1b'
stage=root/'all';(stage/'tools').mkdir(parents=True,exist_ok=True);(stage/'submissions').mkdir(exist_ok=True)
(stage/'conv2d.c').write_bytes(source)
for n in ['bench_conv.c','run.sh','run_diag.sh','tools/mkdiag.py','tools/package_v56.py']:
 (stage/n).write_bytes(subprocess.check_output(['git','show','138dcac:'+n]))
(stage/'README.md').write_text('''# Local K4 indexed vector-store candidate

Source SHA256: d56e8e9b9b427cf1f1b1f91c40f19ffb0e88ce18b52a03d5be0878b3bce9fa1b
Based on upstream 138dcac. K4 uses scalar-indexed vector stores at all three copy sites. The assembly
stride is converted to float units, with remaining byte increments scaled.
All original vector lanes and scalar addresses remain. FMA order, dispatch
and per-call packing are unchanged.
Build: gcc -O3 bench_conv.c conv2d.c -o conv2d_test -lm -fopenmp

conv.zip is normal; conv_nf3.zip forces the existing three-chain control;
conv_diag.zip includes diagnostic probes. These are isolated local archives,
not a published version. Acceptance and performance are tracked separately
in docs/post64-k4-indexed-store.md. Existing 64-byte SVL, external concurrent caller
and allocation-failure limitations remain.
''')
subprocess.run(['python3',str(stage/'tools/package_v56.py')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
diag=(stage/'build/v56/release_diag.c').read_bytes()
operators={'conv':source,'conv_nf3':source.replace(b'#define CONV_NF_REM7 0',b'#define CONV_NF_REM7 3'),'conv_diag':diag}
manifest=[];checks=[]
assert source.count(b'#define CONV_NF_REM7 0')==1
for n,op in operators.items():
 p=stage/'submissions'/f'{n}.zip'
 expected={'conv/conv2d.c':op,'conv/bench_conv.c':(stage/'bench_conv.c').read_bytes(),'conv/run.sh':(stage/('run_diag.sh' if n=='conv_diag' else 'run.sh')).read_bytes(),'conv/README.md':(stage/'README.md').read_bytes()}
 with zipfile.ZipFile(p) as z:
  assert len(z.namelist())==4 and set(z.namelist())==set(expected)
  for member,data in expected.items():assert z.read(member)==data
 manifest.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n')
 checks.append(f'all/{n}: all four members match fixed source/transformation, unchanged benchmark/script, and stage README.')
(out/'archives.sha256').write_text(''.join(manifest));(out/'static_audit.txt').write_text('\n'.join(checks)+'\n')
print(''.join(manifest),end='')
