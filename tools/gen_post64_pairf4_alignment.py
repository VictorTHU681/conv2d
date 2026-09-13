#!/usr/bin/env python3
"""Align the actual short compute entry by changing only hoisted NOP padding."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/post64/pairf4-alignment');out=Path('results/post64/pairf4-alignment')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
base=subprocess.check_output(['git','show','b6ea996:conv2d.c'],text=True)
assert hashlib.sha256(base.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
u4=Path('build/post64/pairf4-current/u4.c').read_text()
assert hashlib.sha256(u4.encode()).hexdigest()=='668e4e03051869703d999b5abe671f6929e3e32e36a637691f43192ca575d99b'
nop='        "nop\\n\\t"\n'
for name,source,count in [('baseline',base,0),('aligned',base,19),('aligned_u4',u4,18)]:
 data=source
 if count:
  a=source.index('static void k16pairf4(');b=source.index('#define PAIRF3_STEP',a)
  fn=source[a:b];old='        ".p2align 7\\n"\n'+nop*count
  assert fn.count(old)==1
  new=old+nop*2;body=fn.replace(old,new,1)
  assert body.replace(new,old,1)==fn
  data=source[:a]+body+source[b:]
 (root/(name+'.c')).write_text(data)
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
files=[root/(n+'.c') for n in ['baseline','aligned','aligned_u4','fbench']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
bench=subprocess.check_output(['git','show','138dcac:bench_conv.c'])
assert hashlib.sha256(bench).hexdigest()=='2548861ae7e29826e454b4c0b098d682f7f04996222e664cd1ea9bc92dd2e927'
(root/'bench_conv.c').write_bytes(bench)
(out/'official_sources.sha256').write_text(''.join(f'{hashlib.sha256((root/n).read_bytes()).hexdigest()}  {root/n}\n' for n in ['baseline.c','aligned.c','bench_conv.c']))
print('Two NOPs added before the short row loop only; aligned baseline otherwise identical to upstream, aligned_u4 otherwise identical to screened U4. No NOP inside the per-row loop. Actual linked alignment and layout must be inspected.')
print((out/'sources.sha256').read_text(),end='')
