#!/usr/bin/env python3
"""Fold K4 scalar-copy input cursor updates into integer load addressing."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/post64/k4-writeback');out=Path('results/post64/k4-writeback')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
s=Path('build/post64/k4-gpr/gpr_loop.c').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='490cd8d972a7d4b5acc7d576f03eaf23c65ed18d08de32aaa64c952c2ce63d95'
a=s.index('static void k4(');b=s.index('#define K5_STEP',a);fn=s[a:b]
x=fn.index('        "71:\\n\\t"');y=fn.index('        "72:\\n\\t"',x);old=fn[x:y]
assert old.count('ldr w23, [x13]')==1 and old.count('add x13, x13, #4')==1
post=old.replace('ldr w23, [x13]','ldr w23, [x13], #4').replace('        "add x13, x13, #4\\n\\t"\n','')
pre='        "sub x13, x13, #4\\n\\t"\n'+post.replace('ldr w23, [x13], #4','ldr w23, [x13, #4]!')
for name,body in [('baseline',old),('post',post),('pre',pre)]:
 (root/(name+'.c')).write_text(s[:a]+fn[:x]+body+fn[y:]+s[b:])
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
files=[root/(n+'.c') for n in ['baseline','post','pre','fbench']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
checks=0
for kw in range(3,401):
 for sh in range(16):
  n=kw+255+sh;f=n//64;t=(n%64)//4;r=n%4;stride=(((n+3)//4+15)&~15)*4+64
  start=4*(64*f+4*t);dst=4*(16*f+t);ref=[(start+4*q,dst+q*stride) for q in range(r)]
  for mode in ['post','pre']:
   cur=start-(4 if mode=='pre' and r else 0);got=[]
   for q in range(r):
    if mode=='pre':cur+=4
    got.append((cur,dst+q*stride))
    if mode=='post':cur+=4
   assert got==ref
   # Post-index ends just past the last word, as before. Pre-index ends on
   # the last word; x13 is reset before the later full-copy/compute phase.
   checks+=1
print(f'{checks} ordered byte-address cases PASS. Baseline here is the previous GPR-loop candidate, not upstream. Pre-index final x13 differs but is dead before reset; no new source bytes or stores.')
print((out/'sources.sha256').read_text(),end='')
