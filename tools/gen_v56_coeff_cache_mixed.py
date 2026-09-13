#!/usr/bin/env python3
"""Historical broad-prefix controls: residual variants also change some input loads."""
from pathlib import Path
import subprocess,hashlib,re
source=subprocess.check_output(['git','show','72b10c2:conv2d.c'],text=True)
root=Path('build/v56/experiments/coefficient-cache');root.mkdir(parents=True,exist_ok=True)
start=source.index('static void k16pair(')
mid=source.index('static void k8(')
end=source.index('// b 表：kind 16:',mid)
pattern=r'ld1w (\{z\d+\.s\}, p0/z, \[x[23][^\]\n]*\])'
def changed(lo,hi):
    part,n=re.subn(pattern,r'ldnt1w \1',source[lo:hi])
    assert n>0
    return source[:lo]+part+source[hi:],n
variants={'baseline':(source,0),'ntwide':changed(start,mid),'ntres':changed(mid,end),'ntall':changed(start,end)}
for name,(s,n) in variants.items():
    p=root/(name+'.c');p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),p)
    # Separate metadata from the sha256sum-compatible manifest.
    Path('results/v56/experiments/coefficient-cache/'+name+'_loads.txt').write_text(f'matrix coefficient load sites changed: {n}\n')
