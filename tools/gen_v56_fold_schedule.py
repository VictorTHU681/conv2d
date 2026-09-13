#!/usr/bin/env python3
"""Interleave independent FMOPA/indexed-FMLA with exactly the same instructions."""
from pathlib import Path
from collections import Counter
import hashlib, subprocess

root=Path('build/v56/experiments/fold-schedule');root.mkdir(parents=True,exist_ok=True)
base=subprocess.check_output(['git','show','3df5c69:conv2d.c'],text=True)
assert hashlib.sha256(base.encode()).hexdigest()=='ebf36923518cb809ae5e65001a700de30b0415956f1d0420a2dffcae45684026'
def weave(s,n):
    start=s.index(f'#define PAIRF{n}_STEP ')
    end=s.index(f'static void k16pairf{n}(',start)
    old=s[start:end];lines=old.splitlines(keepends=True)
    fm=[i for i,x in enumerate(lines) if '"fmopa ' in x]
    fv=[i for i,x in enumerate(lines) if '"fmla ' in x]
    assert len(fm)==4 and len(fv)==2*n and fm+fv==list(range(fm[0],fv[-1]+1))
    ops=[]
    for tile in range(4):
        ops.append(lines[fm[tile]])
        if tile<n: ops.extend(lines[i] for i in fv[2*tile:2*tile+2])
    new=''.join(lines[:fm[0]]+ops+lines[fv[-1]+1:])
    assert Counter(new.splitlines())==Counter(old.splitlines())
    for opcode in ['fmopa','fmla']:
        assert [x for x in new.splitlines() if '"'+opcode+' ' in x]==[x for x in old.splitlines() if '"'+opcode+' ' in x]
    return s[:start]+new+s[end:]
for name,s in [('baseline',base),('f4',weave(base,4)),('f34',weave(weave(base,4),3))]:
    p=root/(name+'.c');p.write_text(s);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
p=root/'fbench.c';p.write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
assert hashlib.sha256(p.read_bytes()).hexdigest()=='e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
