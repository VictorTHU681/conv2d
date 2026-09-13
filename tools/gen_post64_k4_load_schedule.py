#!/usr/bin/env python3
"""Reorder existing K4_STEP loads around unchanged ordered FMOPAs."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/post64/k4-load-schedule');out=Path('results/post64/k4-load-schedule')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','138dcac:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
a=s.index('#define K4_STEP(');b=s.index('#define K4_EV(',a);old=s[a:b];lines=old.splitlines()
assert len(lines)==10 and lines[0]=='#define K4_STEP(PQ, BOFF) \\'
ins=[x.removesuffix(' \\') for x in lines[1:]]
assert all('ld1w' in x for x in ins[:5]) and all('fmopa' in x for x in ins[5:])
assert all(('za'+str(i)+'.s') in ins[5+i] for i in range(4))
orders={'baseline':list(range(9)),'bfirst':[4,0,1,2,3,5,6,7,8],'interleave':[4,0,1,5,2,6,3,7,8]}
for name,order in orders.items():
 assert sorted(order)==list(range(9)) and [i for i in order if i>=5]==[5,6,7,8]
 seen=set()
 for i in order:
  if i>=5:assert 4 in seen and i-5 in seen
  seen.add(i)
 body=lines[0]+'\n'+'\n'.join(ins[i]+(' \\' if j<8 else '') for j,i in enumerate(order))+'\n'
 if name=='baseline':assert body==old
 (root/(name+'.c')).write_text(s[:a]+body+s[b:])
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
files=[root/(n+'.c') for n in [*orders,'fbench']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
print('All nine original instructions occur once per step, every load dominates its consumer, and all four FMOPAs retain their order. Input load order changes; accessed addresses and count do not. No prefetch, copy, arithmetic count or dispatch change.')
print((out/'sources.sha256').read_text(),end='')
