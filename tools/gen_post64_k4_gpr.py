#!/usr/bin/env python3
"""Use integer word loads/stores for bit-preserving K4 scalar tail copies."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/post64/k4-gpr');out=Path('results/post64/k4-gpr')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','138dcac:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
bits=Path('build/post64/k4-scalar/bits.c').read_text()
assert hashlib.sha256(bits.encode()).hexdigest()=='f79dadf140de544ebe6dcd3477868a70bba8d2ebdd8d77f331077aa7d3973c38'
(root/'baseline.c').write_text(s)
for name,source in [('gpr_loop',s),('gpr_bits',bits)]:
 a=source.index('static void k4(');b=source.index('#define K5_STEP',a);fn=source[a:b]
 x=fn.index('        "ptrue p4.s, vl1\\n\\t"');y=fn.index('        "72:\\n\\t"',x)
 old=fn[x:y];new=old.replace('        "ptrue p4.s, vl1\\n\\t"\n','')
 for off in ['',', #4',', #8']:
  new=new.replace('ld1rw {z0.s}, p0/z, [x13'+off+']','ldr w23, [x13'+off+']')
 new=new.replace('st1w {z0.s}, p4, [x20]','str w23, [x20]')
 assert 'z0' not in new and 'p4' not in new
 assert new.count('ldr w23')==new.count('str w23')==(1 if name=='gpr_loop' else 3)
 after=fn[y:];assert '"add x23, x24, x3' in after and '"ldr x23, [%[A], #208]' in after
 (root/(name+'.c')).write_text(source[:a]+fn[:x]+new+fn[y:]+source[b:])
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
files=[root/(n+'.c') for n in ['baseline','gpr_loop','gpr_bits','fbench']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
print('Only K4 scalar tail load/store register class changes, plus PTRUE removal. No float arithmetic. w23 is a dead scratch before later copy/plane pointer initialization. Address/control-flow equivalence inherits the scalar generator; server guard and bitwise tests still required.')
print((out/'sources.sha256').read_text(),end='')
