#!/usr/bin/env python3
"""Check actual K4 indexed-store sequences and arithmetic/load preservation."""
from pathlib import Path
import re,hashlib,argparse
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('build/post64/k4-indexed-store'));parser.add_argument('--prefix',default='');parser.add_argument('--variants',default='full,all');args=parser.parse_args();root=args.root
def read(n):
 p=root/(args.prefix+n+'.dis');rows=[];sym=None
 for line in p.read_text().splitlines():
  m=re.match(r'^[0-9a-f]+ <([^>]+)>:$',line)
  if m:sym=m[1]
  m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',line)
  if m:rows.append((int(m[1],16),m[2],re.sub(r'\s+',' ',m[3].split('//')[0]).strip(),sym))
 print(n,'disassembly SHA256',hashlib.sha256(p.read_bytes()).hexdigest());return rows
base=read('baseline')
def sequence(rs,names):return [(r[1],r[2]) for r in rs if r[2].split()[0] in names]
for name in args.variants.split(','):
 rows=read(name);worker=[r for r in rows if r[3]=='roll_worker'];ops=[r[2] for r in worker]
 for z,d,t in ([(25,'x12','x24')] if name=='full' else [(25,'x12','x24'),(0,'x20','x23'),(0,'x24','x23')]):
  expected=[f'st1w {{z{z}.s}}, p0, [{d}]',f'st1w {{z{z+1}.s}}, p0, [{d}, x3, lsl #2]',f'lsl {t}, x3, #1',
    f'st1w {{z{z+2}.s}}, p0, [{d}, {t}, lsl #2]',f'add {t}, {t}, x3',f'st1w {{z{z+3}.s}}, p0, [{d}, {t}, lsl #2]']
  starts=[i for i in range(len(ops)-5) if ops[i:i+6]==expected];assert len(starts)==1
  print(f'{name}: copy z{z}..z{z+3}, base {d}, float index {t}, starts at 0x{worker[starts[0]][0]:x}: four stores + two integer index operations.')
 assert sum(bool(re.match(r'add x\d+, x\d+, x3, lsl #2$',op)) for op in ops)==(7 if name=='full' else 1)
 assert 'add x20, x20, x3, lsl #2' in ops
 assert sequence(rows,{'fmopa','fmla'})==sequence(base,{'fmopa','fmla'})
 assert sequence(rows,{'ld4w'})==sequence(base,{'ld4w'})
 outer=lambda rs:[r for r in rs if r[3]!='roll_worker']
 print(f'{name}: all FMOPA/FMLA and LD4W words/operands retain their order. Remaining byte-address increments are scaled. Non-worker address/instruction identity={outer(rows)==outer(base)}.')
print('The pinned generator separately converts A.TSB to a float stride while retaining C-side byte offsets. This linked audit does not prove every compiler-generated address or all dynamic accesses; state/guard and original benchmark checks remain necessary.')
