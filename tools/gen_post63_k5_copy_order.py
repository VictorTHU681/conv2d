#!/usr/bin/env python3
"""Permute only the existing interleaved K5 copy instructions on local accepted source."""
from pathlib import Path
from collections import Counter
import hashlib,re,subprocess

root=Path('build/post63/k5-copy-order');out=Path('results/post63/k5-copy-order')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
source=subprocess.check_output(['git','show','ce57939:conv2d.c'],text=True)
assert hashlib.sha256(source.encode()).hexdigest()=='0136da05ea4658fb5792412e95baaec0e38ff299b176e5de681f228bca88da93'
k=source.index('static __attribute__((noinline)) void k5(')
a=source.index('        "61:\\n\\t"\n',k)+len('        "61:\\n\\t"\n')
b=source.index('        "62:\\n\\t"\n',a)
old=source[a:b]
lines=old.splitlines(keepends=True)
assert len(lines)==17
steps=lines[:3];compute_inc=lines[3:7]
prefetch,load=lines[7:9]
stores=lines[9:14];copy_inc=lines[14];loop=lines[15:]
assert steps==[f'        K5_STEP({p}, {i})\n' for i,p in enumerate(['x16','x22','x23'])]
assert 'prfm' in prefetch and 'ld3w' in load
assert [re.search(r'"(\w+)',x)[1] for x in stores]==['st1w','add','st1w','add','st1w']
assert 'subs x20' in loop[0] and 'b.ne 61b' in loop[1]
versions={
    'baseline':old,
    'early':prefetch+load+''.join(steps+compute_inc+stores)+copy_inc+''.join(loop),
    'spread':prefetch+load+steps[0]+stores[0]+stores[1]+steps[1]+stores[2]+stores[3]+steps[2]+stores[4]+''.join(compute_inc)+copy_inc+''.join(loop),
}
macro=source[source.index('#define K5_STEP('):k]
assert not re.search(r'\b(?:x12|x13|x21|x24|z25|z26|z27)\b',macro)
for name,body in versions.items():
    assert Counter(body.splitlines())==Counter(old.splitlines())
    assert re.findall(r'K5_STEP\([^\n]+',body)==re.findall(r'K5_STEP\([^\n]+',old)
    assert body.index('ld3w')<body.index('st1w {z25')<body.index('st1w {z26')<body.index('st1w {z27')
    data=source[:a]+body+source[b:]
    assert data[:a]+old+data[a+len(body):]==source
    (root/(name+'.c')).write_text(data)
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
assert hashlib.sha256((root/'fbench.c').read_bytes()).hexdigest()=='e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
files=[root/(n+'.c') for n in [*versions,'fbench']]
manifest=''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files)
(out/'sources.sha256').write_text(manifest)
print(manifest,end='')
print('Source audit PASS: same instruction/macro multiset, identical compute-step order, unchanged loop control and remaining source. Copy scratch registers are absent from K5_STEP. All variants retain accepted scalar-tail unrolling.')
