#!/usr/bin/env python3
"""Skip shared cutoff reads when local remaining rows already require small chunks."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/v56/experiments/cutoff-local');root.mkdir(parents=True,exist_ok=True)
base=subprocess.check_output(['git','show','8629457:conv2d.c'],text=True)
cutoff=Path('build/v56/experiments/tail-cutoff/cut2.c').read_text()
assert hashlib.sha256(base.encode()).hexdigest()=='1d3f5071d51cd4f8c88720b8d4fa91983515ffd83bdeb4983377a991df2b871a'
assert hashlib.sha256(cutoff.encode()).hexdigest()=='41d1a3a4eddaaa3e972a59dcce2b6770d8aa8556850f3558bdd90fe3c16440b2'
old='g_roll_guided && __atomic_load_n(&g_roll_unfinished.v, __ATOMIC_RELAXED) > (uint64_t)g_roll_cutoff && remaining > 4 * step'
new='g_roll_guided && remaining > 4 * step && __atomic_load_n(&g_roll_unfinished.v, __ATOMIC_RELAXED) > (uint64_t)g_roll_cutoff'
assert cutoff.count(old)==1
local=cutoff.replace(old,new)
assert local.replace(new,old)==cutoff
for name,s in [('baseline',base),('cutoff',cutoff),('local',local)]:
    p=root/f'{name}.c';p.write_text(s);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
p=root/'fbench.c';p.write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
assert hashlib.sha256(p.read_bytes()).hexdigest()=='e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
