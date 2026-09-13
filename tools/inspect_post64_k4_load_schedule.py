#!/usr/bin/env python3
"""Verify each reordered nine-instruction K4_STEP and identical text elsewhere."""
from pathlib import Path
import re,hashlib
root=Path('build/post64/k4-load-schedule')
def read(n):
 p=root/(n+'.dis');rows={};sym=None
 for line in p.read_text().splitlines():
  m=re.match(r'^[0-9a-f]+ <([^>]+)>:$',line)
  if m:sym=m[1]
  m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',line)
  if m:rows[int(m[1],16)]=(m[2],re.sub(r'\s+',' ',m[3].split('//')[0]).strip(),sym)
 print(n,'disassembly SHA256',hashlib.sha256(p.read_bytes()).hexdigest());return rows
b=read('baseline');starts=[]
for a,r in b.items():
 if r[2]!='roll_worker' or r[1]!='fmopa za0.s, p0/m, p0/m, z0.s, z4.s':continue
 if not all(b.get(a+4*i,('','',''))[1]==f'fmopa za{i}.s, p0/m, p0/m, z{i}.s, z4.s' for i in range(4)):continue
 start=a-20
 if not all(b.get(start+4*i,('','',''))[1].startswith(f'ld1w {{z{i}.s}}, p0/z, [') for i in range(5)):continue
 starts.append(start)
begins=[a for a in starts if b[a-4][1]=='sub x15, x15, x20']
assert len(begins)==1
end=next(a for a,r in b.items() if a>begins[0] and r[1]=='lsl w12, w27, #2')
starts=[a for a in starts if begins[0]<=a<end]
assert len(starts)==11
covered={a+4*i for a in starts for i in range(9)}
for name,order in [('bfirst',[4,0,1,2,3,5,6,7,8]),('interleave',[4,0,1,5,2,6,3,7,8])]:
 rows=read(name);assert rows.keys()==b.keys()
 for a in starts:
  assert [rows[a+4*i] for i in range(9)]==[b[a+4*j] for j in order]
 assert {a:r for a,r in rows.items() if a not in covered}=={a:r for a,r in b.items() if a not in covered}
 fmas=lambda rs:[r[:2] for r in rs.values() if r[1].startswith(('fmopa ','fmla '))]
 assert fmas(rows)==fmas(b)
 changed=[a for a in rows if rows[a]!=b[a]]
 print(f'{name}: all 11 K4_STEP blocks match exact load permutation; {len(changed)} changed positions inside those blocks; all other linked instructions and addresses identical.')
print('K4_STEP starts:',', '.join(hex(a) for a in starts))
print('All original operands and instruction counts preserved; all FMOPA/FMLA word/operand ordering preserved. Static scheduling proof is not a throughput or memory-safety test.')
