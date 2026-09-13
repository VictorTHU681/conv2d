#!/usr/bin/env python3
"""Compare outlining alone and outlining plus short-loop unrolling on current upstream."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/post64/pairf4-outline');out=Path('results/post64/pairf4-outline')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
base=subprocess.check_output(['git','show','b6ea996:conv2d.c'],text=True)
assert hashlib.sha256(base.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
u4=Path('build/post64/pairf4-current/u4.c').read_text()
assert hashlib.sha256(u4.encode()).hexdigest()=='668e4e03051869703d999b5abe671f6929e3e32e36a637691f43192ca575d99b'
old='static void k16pairf4(const kp_t* P)'
new='static __attribute__((noinline, aligned(128))) void k16pairf4(const kp_t* P)'
assert base.count(old)==u4.count(old)==1
variants={'baseline':base,'outlined':base.replace(old,new),'outlined_u4':u4.replace(old,new)}
for n,s in variants.items():
    if n!='baseline':assert s.replace(new,old)==(base if n=='outlined' else u4)
    (root/(n+'.c')).write_text(s)
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
files=[root/(n+'.c') for n in [*variants,'fbench']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
print('Only PAIRF4 declaration changed to noinline/aligned(128), with/without already screened U4 body. No dispatch or arithmetic change in outlined-only source. Default upstream remains untouched.')
print((out/'sources.sha256').read_text(),end='')
