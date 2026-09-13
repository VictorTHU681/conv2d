#!/usr/bin/env python3
"""Record actual loop alignment and whether non-worker linked text remains identical."""
from pathlib import Path
import re,hashlib,argparse
parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path('build/post64/pairf4-alignment'))
parser.add_argument('--variants',default='aligned,aligned_u4')
args=parser.parse_args();root=args.root
def read(n):
 p=root/(n+'.dis');rows={};sym=None
 print(n,'disassembly SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
 for l in p.read_text().splitlines():
  m=re.match(r'^[0-9a-f]+ <([^>]+)>:$',l)
  if m:sym=m[1]
  m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',l)
  if m:rows[int(m[1],16)]=(sym,m[2],re.sub(r'\s+',' ',m[3].split('//')[0]).strip())
 return rows
base=read('baseline')
def start(rows,unrolled):
 found=[]
 for a,r in rows.items():
  asm=r[2]
  if (asm=='lsr x15, x7, #2' if unrolled else asm=='mov x15, x7'):
   b=a+(8 if unrolled else 4)
   if rows.get(b+16,('','',''))[2]=='ld1rqw {z4.s}, p0/z, [x13]' and rows.get(b+64,('','',''))[2]=='fmla z17.s, z1.s, z4.s[3]':found.append(b)
 assert len(found)==1;return found[0]
a=start(base,False);assert a%128==120
for name in args.variants.split(','):
 rows=read(name);b=start(rows,name.endswith('u4'));assert b%128==0 and b==a+8
 print(f'{name}: short compute starts at 0x{b:x}, 128-byte aligned; baseline 0x{a:x}.')
 outer=lambda t:{p:r for p,r in t.items() if r[0]!='roll_worker'}
 same=outer(rows)==outer(base)
 print(f'{name}: total instructions {len(rows)} vs baseline {len(base)}; non-roll_worker address/opcode/operand identity={same}.')
 if name=='aligned':
  assert len(rows)==len(base)
  assert same
  changed=[p for p in rows if rows[p]!=base[p]]
  assert changed and all(rows[p][0]==base[p][0]=='roll_worker' for p in changed)
  print(f'{len(changed)} common-address changed positions exclusively inside roll_worker, first 0x{min(changed):x}, last 0x{max(changed):x}.')
  # The complete original 21-instruction step and loop control retain their
  # words after relocation; backward branch has the same displacement.
  assert [rows[b+4*i][1] for i in range(23)]==[base[a+4*i][1] for i in range(23)]
  print('All 23 short-step/loop machine words identical after an eight-byte relocation. Other changed worker regions are not asserted identical.')
print('This audits static linked layout only; timing attribution and runtime memory correctness need separate evidence.')
