#!/usr/bin/env python3
"""Transplant only validated-to-screen U4 function into the freshly pulled source."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/post64/pairf4-current');out=Path('results/post64/pairf4-current')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
current=subprocess.check_output(['git','show','b6ea996:conv2d.c'],text=True)
assert hashlib.sha256(current.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
old=Path('build/post64/pairf4-unroll/baseline.c').read_text()
u4=Path('build/post64/pairf4-unroll/u4.c').read_text()
assert hashlib.sha256(old.encode()).hexdigest()=='0136da05ea4658fb5792412e95baaec0e38ff299b176e5de681f228bca88da93'
assert hashlib.sha256(u4.encode()).hexdigest()=='9da45ffb49f7755bae668a6e68c569ed959e060360f6f2b5b8285574208cca6d'
def fn(s):
 a=s.index('static void k16pairf4(');b=s.index('#define PAIRF3_STEP',a);return a,b,s[a:b]
a,b,body=fn(current)
assert body==fn(old)[2]
new=fn(u4)[2]
combined=current[:a]+new+current[b:]
assert combined[:a]+body+combined[a+len(new):]==current
for name,s in [('baseline',current),('u4',combined),('legacy',u4)]: (root/(name+'.c')).write_text(s)
(root/'fbench.c').write_bytes(Path('build/post64/pairf4-unroll/fbench.c').read_bytes())
paths=[root/(v+'.c') for v in ['baseline','u4','legacy','fbench']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in paths))
print('Upstream PAIRF4 function unchanged from v64. Only the previously screened U4 function substituted; all other upstream source bytes retained. Default K9 weight remains 140; upstream diagnostic additions retained.')
print((out/'sources.sha256').read_text(),end='')
