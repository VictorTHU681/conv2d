#!/usr/bin/env python3
"""Bounded 0..3-scalar K4 copy tails; do not edit the unused K4_CP macro."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/post64/k4-scalar');out=Path('results/post64/k4-scalar')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','138dcac:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
assert s.count('K4_CP(')==1
start=s.index('static void k4(');end=s.index('#define K5_STEP',start)
fn=s[start:end]
old='''        "71:\\n\\t"
        "ld1rw {z0.s}, p0/z, [x13]\\n\\t"
        "st1w {z0.s}, p4, [x20]\\n\\t"
        "add x13, x13, #4\\n\\t"
        "add x20, x20, x3\\n\\t"
        "subs x24, x24, #1\\n\\t"
        "b.ne 71b\\n\\t"
'''
assert fn.count(old)==1
assert 'A.khkw4 = ncp % 4;' in fn
before=fn[:fn.index(old)]
assert before.endswith('        "cbz x24, 72f\\n\\t"\n        "ptrue p4.s, vl1\\n\\t"\n')
after=fn[fn.index(old)+len(old):]
assert after.startswith('        "72:\\n\\t"\n        "ldr x20, [%[A], #304]')
# x13/x20 are reset for serial or interleaved copies. The new tail leaves x24
# as the original remainder, not a zero loop counter; later stores/comparisons
# initialize it before use. No old counter flags may be used by later branches.
assert '        "mov x13, x22\\n\\t"' in after

def emit(xs):return ''.join('        "'+x+'\\n\\t"\n' for x in xs)
head=['ld1rw {z0.s}, p0/z, [x13]','st1w {z0.s}, p4, [x20]']
second=['ld1rw {z0.s}, p0/z, [x13, #4]','add x20, x20, x3','st1w {z0.s}, p4, [x20]']
third=['ld1rw {z0.s}, p0/z, [x13, #8]','add x20, x20, x3','st1w {z0.s}, p4, [x20]']
bodies={'baseline':old,'direct':emit(head+['cmp x24, #1','b.eq 72f']+second+['cmp x24, #2','b.eq 72f']+third),'bits':emit(head+['tbz x24, #1, 72f']+second+['tbz x24, #0, 72f']+third)}
for name,body in bodies.items():
 new=fn.replace(old,body,1)
 assert new.replace(body,old,1)==fn
 (root/(name+'.c')).write_text(s[:start]+new+s[end:])
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
files=[root/(n+'.c') for n in [*bodies,'fbench']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
checks=0
for kw in range(3,401):
 for sh in range(16):
  n=kw+255+sh;full=n//64;tail=(n%64)//4;rem=n%4
  stride=(((n+3)//4+15)&~15)*4+64
  src=full*64+tail*4;dst=full*16+tail
  ref=[(src+q,dst+q*(stride//4)) for q in range(rem)]
  for mode in ['direct','bits']:
   got=[]
   if rem:
    got.append((src,dst))
    if (rem!=1 if mode=='direct' else rem&2):
     got.append((src+1,dst+stride//4))
     if (rem!=2 if mode=='direct' else rem&1):got.append((src+2,dst+2*(stride//4)))
   assert got==ref
   assert all(src<=r<n for r,w in got)
   checks+=1
print(f'{checks} exact ordered scalar read/write address cases PASS (KW 3..400, 16 alignments, two candidates). No FMA, prefetch or full/tail-vector copies changed. This models equivalence to the old scalar interval, not all assembly accesses.')
print((out/'sources.sha256').read_text(),end='')
