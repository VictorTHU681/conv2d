#!/usr/bin/env python3
"""Try one predicated contiguous load and byte-offset scatter for K4 tail."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/post64/k4-scatter');out=Path('results/post64/k4-scatter')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','138dcac:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
a=s.index('static void k4(');b=s.index('#define K5_STEP',a);fn=s[a:b]
x=fn.index('        "ptrue p4.s, vl1\\n\\t"');y=fn.index('        "72:\\n\\t"',x)
old=fn[x:y]
assert old.count('ld1rw')==1 and 'b.ne 71b' in old
body=''.join('        "'+i+'\\n\\t"\n' for i in [
 'whilelo p4.s, xzr, x24','ld1w {z0.s}, p4/z, [x13]',
 'index z1.s, #0, w3','st1w {z0.s}, p4, [x20, z1.s, uxtw]'])
new=fn[:x]+body+fn[y:]
assert new.replace(body,old,1)==fn
(root/'baseline.c').write_text(s)
(root/'scatter.c').write_text(s[:a]+new+s[b:])
p=Path('build/post64/k4-scalar/bits.c');assert hashlib.sha256(p.read_bytes()).hexdigest()=='f79dadf140de544ebe6dcd3477868a70bba8d2ebdd8d77f331077aa7d3973c38'
(root/'bits.c').write_bytes(p.read_bytes())
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
files=[root/(n+'.c') for n in ['baseline','scatter','bits','fbench']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
checks=0
for kw in range(3,401):
 for sh in range(16):
  n=kw+255+sh;full=n//64;tail=(n%64)//4;rem=n%4
  stride=(((n+3)//4+15)&~15)*4+64
  src=4*(full*64+tail*4);dst=4*(full*16+tail)
  scalar=[(src+4*q,dst+stride*q) for q in range(rem)]
  scatter=[(src+4*q,dst+((q*stride)&0xffffffff)) for q in range(16) if q<rem]
  assert scalar==scatter and len(set(w for r,w in scatter))==rem
  assert all(src<=r<4*n and q*stride<2**32 for q,(r,w) in enumerate(scatter))
  checks+=1
print(f'{checks} byte-address equivalence cases PASS. Inactive lanes excluded; this model is not a dynamic guard test or a proof for all assembly accesses.')
print((out/'sources.sha256').read_text(),end='')
