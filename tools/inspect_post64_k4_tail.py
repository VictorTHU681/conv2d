#!/usr/bin/env python3
"""Inspect linked K4 tail blocks and preserve the complete worker FMA sequence."""
from pathlib import Path
import argparse,re,hashlib
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('build/post64/k4-scalar'));p.add_argument('--variants',default='direct,bits');p.add_argument('--prefix',default='');args=p.parse_args()
def read(name):
 path=args.root/(args.prefix+name+'.dis');rows=[];sym=None
 for line in path.read_text().splitlines():
  m=re.match(r'^[0-9a-f]+ <([^>]+)>:$',line)
  if m:sym=m[1]
  m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',line)
  if m:rows.append((int(m[1],16),m[2],re.sub(r'\s+',' ',m[3].split('//')[0]).strip(),sym))
 print(name,'disassembly SHA256',hashlib.sha256(path.read_bytes()).hexdigest());return rows
base=read('baseline')
def tail(rows):
 found=[]
 for i,r in enumerate(rows):
  if r[3]=='roll_worker' and r[2]=='ldr x24, [x18, #272]' and rows[i-1][2]=='add x20, x20, x24, lsl #2' and rows[i-2][2]=='add x13, x13, x24, lsl #4':
   for j in range(i+1,i+24):
    if rows[j][2]=='ldr x20, [x18, #304]':found.append(rows[i:j+1]);break
 assert len(found)==1;return found[0]
def arithmetic(rows):return [(r[1],r[2]) for r in rows if r[3]=='roll_worker' and r[2].split()[0] in ['fmopa','fmla','fadd','fmul','fsub','fmad']]
b=tail(base)
for name in args.variants.split(','):
 rows=read(name);t=tail(rows);ops=[r[2].split()[0] for r in t[2:-1]]
 expected={'direct':['ptrue','ld1rw','st1w','cmp','b.eq','ld1rw','add','st1w','cmp','b.eq','ld1rw','add','st1w'],
 'bits':['ptrue','ld1rw','st1w','tbz','ld1rw','add','st1w','tbz','ld1rw','add','st1w'],
 'scatter':['whilelo','ld1w','index','st1w'],
 'gpr_loop':['ldr','str','add','add','subs','b.ne'],
 'gpr_bits':['ldr','str','tbz','ldr','add','str','tbz','ldr','add','str'],
 'post':['ldr','str','add','subs','b.ne'],
 'pre':['sub','ldr','str','add','subs','b.ne']}[name]
 assert ops==expected
 assert arithmetic(rows)==arithmetic(base)
 for r in t:
  if r[2].split()[0] in ['cbz','b.eq','tbz']:assert int(r[2].split(' <')[0].split()[-1],16)==t[-1][0]
 if name in ['bits','gpr_bits']:
  assert [r[2].split(', ')[1] for r in t if r[2].startswith('tbz')]==['#1','#0']
 if name=='scatter':assert [r[2] for r in t[2:-1]]==['whilelo p4.s, xzr, x24','ld1w {z0.s}, p4/z, [x13]','index z1.s, #0, w3','st1w {z0.s}, p4, [x20, z1.s, uxtw]']
 elif name in ['post','pre']:
  load='ldr w23, [x13], #4' if name=='post' else 'ldr w23, [x13, #4]!'
  assert [r[2] for r in t if r[2].startswith('ldr w23')]==[load]
  assert [r[2] for r in t if r[2].startswith('str ')]==['str w23, [x20]']
  if name=='pre':assert t[2][2]=='sub x13, x13, #0x4'
  assert int(t[-2][2].split()[1],16)==t[2 if name=='post' else 3][0]
 elif name.startswith('gpr_'):
  loads=['ldr w23, [x13]','ldr w23, [x13, #4]','ldr w23, [x13, #8]']
  assert [r[2] for r in t if r[2].startswith('ldr w23')]==(loads[:1] if name=='gpr_loop' else loads)
  assert [r[2] for r in t if r[2].startswith('str ')]==['str w23, [x20]']*(1 if name=='gpr_loop' else 3)
  if name=='gpr_loop':assert int(t[-2][2].split()[1],16)==t[2][0]
 else:assert [r[2] for r in t if r[2].startswith('ld1rw')]==['ld1rw {z0.s}, p0/z, [x13]','ld1rw {z0.s}, p0/z, [x13, #4]','ld1rw {z0.s}, p0/z, [x13, #8]']
 outer=lambda rs:[r for r in rs if r[3]!='roll_worker']
 print(f'{name}: tail 0x{t[0][0]:x}..0x{t[-1][0]:x}; {len(t)-3} body instructions vs {len(b)-3}; worker arithmetic opcode/operand sequence identical ({len(arithmetic(rows))} instructions).')
 print(f'Total instructions {len(rows)} vs {len(base)}; non-worker address/opcode/operand identity={outer(rows)==outer(base)}.')
 by_address={r[0]:r for r in rows};base_address={r[0]:r for r in base}
 if by_address.keys()==base_address.keys():
  changed=[a for a in by_address if by_address[a]!=base_address[a]]
  print(f'Common-address changes: {len(changed)} positions, 0x{min(changed):x}..0x{max(changed):x}.')
  if name in ['gpr_loop','post','pre']:
   compute=next(r[0] for r in base if r[0]>b[-1][0] and r[2]=='ld1w {z0.s}, p0/z, [x16]')
   assert all(b[0][0]<=a<compute for a in changed)
   print(f'All changes confined to K4 scalar tail / following setup before compute entry 0x{compute:x}; every instruction/address elsewhere identical.')
 for r in t:print(f'  {r[0]:x}: {r[1]} {r[2]}')
print('Static linked instruction audit only. Correctness and performance require the separate server tests; layout changes are not a proven timing mechanism.')
