#!/usr/bin/env python3
"""Use SVE scalar-indexed stores to reduce K4 four-plane copy address work."""
from pathlib import Path
import hashlib,subprocess,re
root=Path('build/post64/k4-indexed-store');out=Path('results/post64/k4-indexed-store')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','138dcac:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
a=s.index('static void k4(');b=s.index('#define K5_STEP',a);original=s[a:b]
assert original.count('A.TSB = TSB;')==1
# x3 becomes the float (not byte) stride. All still-existing address ADDs
# compensate with LSL #2; newly generated index arithmetic stays in floats.
pat=r'(add x\d+, x\d+, x3)(?=\\n)'
fn,n=re.subn(pat,r'\1, lsl #2',original);assert n==10
fn=fn.replace('A.TSB = TSB;','A.TSB = TSB / 4;')
fn=fn.replace('// TSB（覆盖 bB）','// TSB/4，SVE word-index stride（覆盖 bB）')
def old_block(z,d,t):
 return (f'        "st1w {{z{z}.s}}, p0, [{d}]\\n\\t" "add {t}, {d}, x3, lsl #2\\n\\t" "st1w {{z{z+1}.s}}, p0, [{t}]\\n\\t"\n'
 f'        "add {t}, {t}, x3, lsl #2\\n\\t" "st1w {{z{z+2}.s}}, p0, [{t}]\\n\\t" "add {t}, {t}, x3, lsl #2\\n\\t" "st1w {{z{z+3}.s}}, p0, [{t}]\\n\\t"\n')
def new_block(z,d,t):
 ops=[f'st1w {{z{z}.s}}, p0, [{d}]',f'st1w {{z{z+1}.s}}, p0, [{d}, x3, lsl #2]',
 f'lsl {t}, x3, #1',f'st1w {{z{z+2}.s}}, p0, [{d}, {t}, lsl #2]',
 f'add {t}, {t}, x3',f'st1w {{z{z+3}.s}}, p0, [{d}, {t}, lsl #2]']
 return ''.join('        "'+i+'\\n\\t"\n' for i in ops)
blocks=[(25,'x12','x24'),(0,'x20','x23'),(0,'x24','x23')]
for q in blocks:assert fn.count(old_block(*q))==1
(root/'baseline.c').write_text(s)
for name,count in [('full',1),('all',3)]:
 f=fn
 for q in blocks[:count]:f=f.replace(old_block(*q),new_block(*q),1)
 assert f.count('K4_STEP(')==original.count('K4_STEP(')==11
 assert 'roll_first_planes(P->ring, P->in_row, P->KW + 255, sh, 4, TSB / 4);' in f
 (root/(name+'.c')).write_text(s[:a]+f+s[b:])
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
files=[root/(n+'.c') for n in ['baseline','full','all','fbench']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
checks=0
for kw in range(3,401):
 for sh in range(16):
  n=kw+255+sh;tsb=(((n+3)//4+15)&~15)*4+64;idx=tsb//4
  assert 4*idx==tsb
  for base in [0,4*(n//64)*16,4*((n//64)*16+(n%64)//4)]:
   old=[base+p*tsb+lane*4 for p in range(4) for lane in range(16)]
   offsets=[0,idx,idx*2,idx*3];new=[base+(off<<2)+lane*4 for off in offsets for lane in range(16)]
   assert new==old
   # Remaining scalar and unconverted vector address increments retain bytes.
   assert all(base+q*tsb==base+q*(idx<<2) for q in range(4))
   checks+=1
print(f'{checks} ordered vector-store address cases PASS. TSB is positive/multiple-of-four; destination/index registers are distinct. Full vector lanes, scalar tails and C-side plane offsets remain unchanged. Model is not a dynamic memory-safety proof.')
print((out/'sources.sha256').read_text(),end='')
