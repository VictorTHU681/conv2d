#!/usr/bin/env python3
"""Move scalar-coefficient production earlier without changing loop size or arithmetic order."""
from pathlib import Path
from collections import Counter
import hashlib,subprocess
source=subprocess.check_output(['git','show','93163b4:conv2d.c'],text=True)
a=source.index('static void k16pairf(');b=source.index('\n}\n',a)+3
f=source[a:b];start=f.index('        "2:\\n\\t"\n')+len('        "2:\\n\\t"\n')
end=f.index('        "b.ne 2b\\n\\t"\n',start)+len('        "b.ne 2b\\n\\t"\n')
body=f[start:end]
scalar='        "ld1rw {z4.s}, p0/z, [x13]\\n\\t"\n'
assert body.count(scalar)==1
early=scalar+body.replace(scalar,'')
fmla0='        "fmla z10.s, p0/m, z0.s, z4.s\\n\\t"\n'
fmla1='        "fmla z11.s, p0/m, z1.s, z4.s\\n\\t"\n'
weave=early.replace(fmla0,'').replace(fmla1,'')
for tile,extra in [(0,fmla0),(1,fmla1)]:
    marker=f'        "fmopa za{tile}.s, p0/m, p0/m, z{tile}.s, z2.s\\n\\t"\n'
    assert weave.count(marker)==1
    weave=weave.replace(marker,marker+extra)
root=Path('build/v56/experiments/k33-schedule');root.mkdir(parents=True,exist_ok=True)
for name,part in [('baseline',body),('early',early),('weave',weave)]:
    assert Counter(part.splitlines())==Counter(body.splitlines())
    s=source[:a]+f[:start]+part+f[end:]+source[b:]
    p=root/(name+'.c');p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),p)
