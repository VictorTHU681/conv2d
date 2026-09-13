#!/usr/bin/env python3
"""Reorder K4 output slice extraction, zeroing and interleaved store."""
from pathlib import Path
from collections import Counter
import hashlib,subprocess
root=Path('build/post64/k4-events');out=Path('results/post64/k4-events')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','138dcac:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
a=s.index('#define K4_EV(');b=s.index('static void k4(',a);old=s[a:b];lines=old.splitlines()
assert len(lines)==10 and lines[0]=='#define K4_EV(T) \\'
ops=[x.removesuffix(' \\') for x in lines[1:]]
assert all('mova z' in x for x in ops[:4]) and 'st4w' in ops[4] and all('mova za' in x for x in ops[5:])
orders={'baseline':list(range(9)),'clearfirst':[0,1,2,3,5,6,7,8,4],'paired':[0,5,1,6,2,7,3,8,4]}
for name,order in orders.items():
 assert Counter(order)==Counter(range(9))
 for j in range(4):assert order.index(j)<order.index(j+5) and order.index(j)<order.index(4)
 # All four slices are cleared before macro exit; z0..3 are stored before
 # the next tile reuses them. Pairing clears only the slice already read.
 body=lines[0]+'\n'+'\n'.join(ops[i]+(' \\' if j<8 else '') for j,i in enumerate(order))+'\n'
 if name=='baseline':assert body==old
 (root/(name+'.c')).write_text(s[:a]+body+s[b:])
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
files=[root/(n+'.c') for n in [*orders,'fbench']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
print('Per-tile nine-instruction multiset and slice read-before-clear/store dependencies validate. All four clears complete before next row, and output store precedes vector reuse. No arithmetic, memory operands, dispatch or packing changes.')
print((out/'sources.sha256').read_text(),end='')
