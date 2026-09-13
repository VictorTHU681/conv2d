#!/usr/bin/env python3
"""Preserve upstream archives and stage separate alignment candidates for local checks."""
from pathlib import Path
import hashlib,subprocess,zipfile
root=Path('build/post64/package-check');out=Path('results/post64/package-check')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
upstream=subprocess.check_output(['git','show','138dcac:conv2d.c'])
assert hashlib.sha256(upstream).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
aligned=Path('build/post64/pairf4-alignment/aligned.c').read_bytes()
assert hashlib.sha256(aligned).hexdigest()=='d542ee52d8a1b3262dabee98f3ef27b6bd174aeba12a0bf4ec86e1862c7e6c67'
assert aligned.count(b'        "nop\\n\\t"\n')==upstream.count(b'        "nop\\n\\t"\n')+2
# The alignment generator pins and reverses the specific PAIRF4 replacement.
manifest=[];checks=[]
for variant,source in [('upstream',upstream),('aligned',aligned)]:
 stage=root/variant;(stage/'submissions').mkdir(parents=True,exist_ok=True);(stage/'tools').mkdir(exist_ok=True)
 (stage/'conv2d.c').write_bytes(source)
 for n in ['bench_conv.c','run.sh','run_diag.sh','tools/mkdiag.py','tools/package_v56.py']:
  (stage/n).write_bytes(subprocess.check_output(['git','show','138dcac:'+n]))
 if variant=='upstream':
  for n in ['conv','conv_nf3','conv_diag']:(stage/'submissions'/f'{n}.zip').write_bytes(subprocess.check_output(['git','show','138dcac:submissions/'+n+'.zip']))
  with zipfile.ZipFile(stage/'submissions/conv.zip') as z:(stage/'README.md').write_bytes(z.read('conv/README.md'))
  subprocess.run(['python3',str(stage/'tools/mkdiag.py'),str(stage/'conv2d.c'),str(stage/'diagnostic.c')],check=True,stdout=subprocess.DEVNULL)
  diagnostic=(stage/'diagnostic.c').read_bytes()
 else:
  (stage/'README.md').write_text(f'''# Local PAIRF4 short-loop alignment candidate

Source SHA256: {hashlib.sha256(source).hexdigest()}
Based on upstream 138dcac / 08400a76. Only two hoisted NOPs are added before
PAIRF4 short row processing so its linked compute loop starts on 128 bytes.
No compute unrolling or outlined kernel is included. Input reads, output
mapping and every FMA chain are unchanged. Build and run scripts are unchanged:
gcc -O3 bench_conv.c conv2d.c -o conv2d_test -lm -fopenmp

conv.zip is normal; conv_nf3.zip forces the existing three-chain control;
conv_diag.zip includes diagnostic probes. This is an isolated local candidate,
not a published release. Original comparative performance is still pending.
Existing 64-byte SVL and external-concurrent-caller/allocation-failure limits
remain. No blanket correctness or compliance claim is made.
''')
  subprocess.run(['python3',str(stage/'tools/package_v56.py')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  diagnostic=(stage/'build/v56/release_diag.c').read_bytes()
 operators={'conv':source,'conv_nf3':source.replace(b'#define CONV_NF_REM7 0',b'#define CONV_NF_REM7 3'),'conv_diag':diagnostic}
 for n,operator in operators.items():
  p=stage/'submissions'/f'{n}.zip'
  expected={'conv/conv2d.c':operator,'conv/bench_conv.c':(stage/'bench_conv.c').read_bytes(),'conv/run.sh':(stage/('run_diag.sh' if n=='conv_diag' else 'run.sh')).read_bytes(),'conv/README.md':(stage/'README.md').read_bytes()}
  with zipfile.ZipFile(p) as z:
   assert len(z.namelist())==4 and set(z.namelist())==set(expected)
   for member,b in expected.items():assert z.read(member)==b,(variant,n,member)
  manifest.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n')
  checks.append(f'{variant}/{n}: all four members match intended source, unchanged benchmark/script, and stage README.')
(out/'archives.sha256').write_text(''.join(manifest));(out/'static_audit.txt').write_text('\n'.join(checks)+'\n')
print(''.join(manifest),end='');print('\n'.join(checks))
