#!/usr/bin/env python3
"""Reuse the otherwise unused x25 for invocation-local folded output phase."""
from pathlib import Path
import hashlib,re,subprocess
root=Path('build/v56/experiments/fold-param');root.mkdir(parents=True,exist_ok=True)
base=subprocess.check_output(['git','show','3df5c69:conv2d.c'],text=True)
assert hashlib.sha256(base.encode()).hexdigest()=='ebf36923518cb809ae5e65001a700de30b0415956f1d0420a2dffcae45684026'
lines=base.splitlines(keepends=True);macros={};i=0
while i<len(lines):
    m=re.match(r'#define (\w+)\b',lines[i])
    if m:
        text=lines[i]
        while lines[i].rstrip().endswith('\\'):
            i+=1;text+=lines[i]
        macros[m[1]]=text
    i+=1
load=macros['LOAD_ARGS']
assert re.findall(r'\b[wx]25\b',load)==['x25']
old='ldr x25, [%[A], #120]'
assert load.count(old)==1
cached_load=load.replace('#define LOAD_ARGS ', '#define LOAD_ARGS_FOLD_CF ').replace(old,'ldr x25, [%[A], #216]')
def function(s,n):
    a=s.index(f'static void k16pairf{n}(');b=s.index('\n}\n',a)+3
    return a,b,s[a:b]
for n in [3,4]:
    _,_,body=function(base,n)
    assert not re.search(r'\b[wx]25\b',body)
    pending=set(re.findall(r'\b[A-Z][A-Z0-9_]*\b',body))&macros.keys();seen=set()
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name)
        if name in ['XCLOB','LOAD_ARGS']:continue
        assert not re.search(r'\b[wx]25\b',macros[name]),name
        pending.update((set(re.findall(r'\b[A-Z][A-Z0-9_]*\b',macros[name]))&macros.keys())-seen)
    assert 'LOAD_ARGS' in seen and 'XCLOB' in seen
def candidate(ns):
    s=base.replace(load,load+cached_load,1)
    for n in ns:
        a,b,body=function(s,n)
        assert body.count('        LOAD_ARGS\n')==1
        body=body.replace('        LOAD_ARGS\n','        LOAD_ARGS_FOLD_CF\n')
        if n==3:
            assert body.count('ldr x24, [%[A], #216]')==1
            body=body.replace('ldr x24, [%[A], #216]','mov x24, x25')
        s=s[:a]+body+s[b:]
        if n==4:
            tail=macros['PAIRF4_TAIL'];assert s.count(tail)==1
            assert tail.count('ldr x24, [%[A], #216]')==1
            s=s.replace(tail,tail.replace('ldr x24, [%[A], #216]','mov x24, x25'))
    return s
for name,s in [('baseline',base),('cf4',candidate([4])),('cf34',candidate([4,3]))]:
    p=root/(name+'.c');p.write_text(s);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
p=root/'fbench.c';p.write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
assert hashlib.sha256(p.read_bytes()).hexdigest()=='e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
