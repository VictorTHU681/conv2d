#!/usr/bin/env python3
"""Check exact non-F3 worker bytes and canonicalized island control flow."""
from pathlib import Path
import re,hashlib,difflib,collections
root=Path('build/post64/pairf3-island');out=Path('results/post64/pairf3-island')
def read(n):
 p=root/f'official_{n}.dis';d={};sym=''
 for l in p.read_text().splitlines():
  m=re.match('^[0-9a-f]+ <([^>]+)>:$',l)
  if m:sym=m[1]
  m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',l)
  if m:
   t=re.sub(r'\s+',' ',m[3].split('//')[0]).strip()
   d[int(m[1],16)]=(m[2],t,sym)
 print(n,'disassembly SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
 return d
b,u,c=[read(n) for n in ['baseline','u4','island']]
starts=[a-60 for a,r in b.items() if r[2]=='roll_worker' and r[1]=='add x13, x13, #0x10' and b[a-4][1]=='fmla z15.s, z1.s, z4.s[2]']
assert len(starts)==2
start=starts[1];end=start+21*4
assert c[start][1].startswith('b ')
entry=int(c[start][1].split()[1],16)
assert all(c[a][1]=='nop' for a in range(start+4,end,4))
worker={a:r for a,r in b.items() if r[2]=='roll_worker'}
assert set(worker)=={a for a,r in c.items() if r[2]=='roll_worker'}
assert all(c[a][0]==r[0] for a,r in worker.items() if not start<=a<end)
assert b[end][1]==c[end][1]=='cmp x2, x5'
us=[a for a,r in u.items() if r[1]=='lsr x12, x15, #2'];assert len(us)==1
us=us[0];ue=us
while u[ue][1]!='cmp x2, x5':ue+=4
assert c[entry][1]=='lsr x12, x15, #2'
exit_addr=entry+ue-us
assert c[exit_addr][1].startswith(f'b {end:x} ')
def canonical(t,pc):
 # Canonicalize direct branch target by relative displacement, keep registers.
 if re.match(r'^(b(?:\.\w+)?|cbz|cbnz) ',t):
  m=re.search(r'([0-9a-f]+) <[^>]+>$',t);assert m,t
  t=t[:m.start()]+f'@{int(m[1],16)-pc:+d}'
 return t
assert [canonical(u[a][1],a) for a in range(us,ue,4)]==[canonical(c[a][1],a) for a in range(entry,exit_addr,4)]
changed=collections.Counter(r[2] for a,r in b.items() if a in c and c[a][0]!=r[0])
print(f'PASS: exactly 21 original F3 instruction slots at 0x{start:x}..0x{end-4:x} become entry branch plus 20 unreachable NOPs.')
print(f'PASS: all other {len(worker)-21} roll_worker instruction words and addresses identical to upstream, including other kernel paths.')
print(f'PASS: island 0x{entry:x}..0x{exit_addr:x}; all {((ue-us)//4)} original u4 setup/compute/remainder instructions and relative branch targets identical; exit jumps to original row-wrap 0x{end:x}.')
print('Original-address machine-word differences by symbol:',dict(changed))
print('Non-worker constant addresses and final sections move; not a whole-binary identity claim. Objdump attributes appended code to nearest preceding symbol; it is reached by direct branch, not a call to that function. No dynamic correctness/performance claim.')
s,t=[(root/(n+'.c')).read_text() for n in ['baseline','island']]
out.joinpath('source.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='baseline.c',tofile='island.c')))
