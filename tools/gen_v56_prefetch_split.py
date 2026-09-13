#!/usr/bin/env python3
"""Separate input/output prefetch configuration for factorial attribution only."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/v56/experiments/prefetch-split');root.mkdir(parents=True,exist_ok=True)
base=subprocess.check_output(['git','show','3df5c69:conv2d.c'],text=True)
assert hashlib.sha256(base.encode()).hexdigest()=='ebf36923518cb809ae5e65001a700de30b0415956f1d0420a2dffcae45684026'
edits=[
    ('static int g_pf_fresh = 1;', 'static int g_pf_fresh = 1;\nstatic long g_roll_pdin=3, g_roll_pdout=3;'),
    ('    g_knobs.roll_pd = env_int("CONV_ROLL_PD", 3);',
     '    g_roll_pdin = env_int("CONV_ROLL_PDIN", env_int("CONV_ROLL_PD", 3));\n'
     '    g_roll_pdout = env_int("CONV_ROLL_PDOUT", env_int("CONV_ROLL_PD", 3));\n'
     '    g_knobs.roll_pd = env_int("CONV_ROLL_PD", 3);'),
    ('A->pf = g_roll_pd * P->rsb;', 'A->pf = g_roll_pdin * P->rsb;'),
    ('A->PD = g_roll_pd;', 'A->PD = g_roll_pdout;'),
    ('A->pfo = g_roll_pd * P->osb;', 'A->pfo = g_roll_pdout * P->osb;'),
]
s=base
for old,new in edits:
    assert s.count(old)==1,old;s=s.replace(old,new)
undo=s
for old,new in reversed(edits):
    assert undo.count(new)==1;undo=undo.replace(new,old)
assert undo==base
for name,data in [('split.c',s.encode()),('fbench.c',subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))]:
    p=root/name;p.write_bytes(data);print(hashlib.sha256(data).hexdigest(),p)
