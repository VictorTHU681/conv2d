#!/usr/bin/env python3
"""Verify reordered K4 output/clear blocks and identical linked code elsewhere."""
from pathlib import Path
import re,hashlib,argparse
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('build/post64/k4-events'));parser.add_argument('--prefix',default='');parser.add_argument('--variants',default='clearfirst,paired');args=parser.parse_args();root=args.root
def read(n):
 p=root/(args.prefix+n+'.dis');rows={};sym=None
 for line in p.read_text().splitlines():
  m=re.match(r'^[0-9a-f]+ <([^>]+)>:$',line)
  if m:sym=m[1]
  m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',line)
  if m:rows[int(m[1],16)]=(m[2],re.sub(r'\s+',' ',m[3].split('//')[0]).strip(),sym)
 print(n,'disassembly SHA256',hashlib.sha256(p.read_bytes()).hexdigest());return rows
b=read('baseline');starts=[]
for a,r in b.items():
 if r[2]=='roll_worker' and r[1]=='lsl w12, w27, #2':starts.append(a+4)
assert len(starts)==1
start=starts[0]
# MOVA disassembles as MOV; verify actual ZA slices rather than matching only
# instruction mnemonics shared by many other kernels.
for t in range(4):
 for j in range(4):
  assert b[start+4*(t*9+j)][1]==f'mov z{j}.s, p0/m, za{t}v.s[w12, {j}]'
  assert b[start+4*(t*9+5+j)][1]==f'mov za{t}v.s[w12, {j}], p0/m, z31.s'
 assert b[start+4*(t*9+4)][1].startswith('st4w {z0.s-z3.s}, p0, [x20')
covered={start+4*i for i in range(36)}
orders={'clearfirst':[0,1,2,3,5,6,7,8,4],'paired':[0,5,1,6,2,7,3,8,4]}
for name in args.variants.split(','):
 order=orders[name]
 r=read(name);assert r.keys()==b.keys()
 for t in range(4):
  a=start+36*t
  assert [r[a+4*i] for i in range(9)]==[b[a+4*j] for j in order]
 assert {a:v for a,v in r.items() if a not in covered}=={a:v for a,v in b.items() if a not in covered}
 print(f'{name}: all four nine-instruction event blocks match exact permutation; all other linked addresses/instructions identical; {sum(r[a]!=b[a] for a in r)} changed positions at 0x{start:x}..0x{start+140:x}.')
print('Every slice is read before clear; all four result vectors are captured before the same ST4W. All clears finish before the next row. Static dependencies do not replace dynamic state/guard or performance tests.')
