#!/usr/bin/env python3
"""K9 two-pair unroll and alternating-register software pipeline."""
from pathlib import Path
import subprocess,hashlib
source=subprocess.check_output(['git','show','72b10c2:conv2d.c'],text=True)
root=Path('build/v59');root.mkdir(parents=True,exist_ok=True)
def emit(xs):return ''.join('        "'+x+'\\n\\t"\n' for x in xs)
banks=[([1,3,5,7],[8,9]),([10,11,12,13],[14,15])]
def loads(bank,advance=False):
    odd,coef=banks[bank]
    xs=['add x21, x25, #4'] if advance else []
    base='x21' if advance else 'x25'
    xs += [f'ld1w {{z{r}.s}}, p0/z, [{base}, #{i}, mul vl]' for i,r in enumerate(odd)]
    xs += [f'ld1w {{z{r}.s}}, p0/z, [x2, #{i+(2 if advance else 0)}, mul vl]' for i,r in enumerate(coef)]
    return xs

def pair(bank=0,load=True,preload=False):
    odd,coef=banks[bank]
    xs=loads(bank) if load else []
    xs+=['ld1rw {z24.s}, p0/z, [x13]','add x13, x13, #4']
    for i in range(4):
        xs += [f'fmopa za{i}.s, p0/m, p0/m, z{2*i}.s, z{coef[0]}.s',
               f'fmla z{16+2*i}.s, p0/m, z{2*i}.s, z24.s',
               f'fmla z{17+2*i}.s, p0/m, z{odd[i]}.s, z24.s']
    xs+=['ld1rw {z24.s}, p0/z, [x13]','add x13, x13, #4','add x21, x16, #4']
    xs += [f'ld1w {{z{2*i}.s}}, p0/z, [x21, #{i}, mul vl]' for i in range(4)]
    if preload:
        no,nc=banks[1-bank]
        xs+=['add x21, x25, #4']
        xs += [f'ld1w {{z{r}.s}}, p0/z, [x2, #{i+2}, mul vl]' for i,r in enumerate(nc)]
    for i in range(4):
        xs += [f'fmopa za{i}.s, p0/m, p0/m, z{odd[i]}.s, z{coef[1]}.s',
               f'fmla z{16+2*i}.s, p0/m, z{odd[i]}.s, z24.s',
               f'fmla z{17+2*i}.s, p0/m, z{2*i}.s, z24.s']
        if preload:xs += [f'ld1w {{z{no[i]}.s}}, p0/z, [x21, #{i}, mul vl]']
    xs+=['add x16, x16, #4','add x25, x25, #4','add x2, x2, #128']
    return xs

def variant(pipeline):
    a=source.index('static __attribute__((noinline)) void k8f(')
    b=source.index('\n}\n',a)+3
    f=source[a:b]
    f=f.replace(emit(['mov x15, x7']),emit(['lsr x15, x7, #1']))
    lo=f.index(emit(['2:'])); hi=f.index(emit(['b.ne 2b']),lo)+len(emit(['b.ne 2b']))
    xs=(loads(0) if pipeline else [])+['cbz x15, 61f','2:']
    if pipeline:xs+=pair(0,False,True)+pair(1,False,True)
    else:xs+=pair()+pair()
    xs+=['subs x15, x15, #1','b.ne 2b','61:','tbz x7, #0, 62f']
    xs+=pair(0,not pipeline,False)
    xs+=['62:']
    f=f[:lo]+emit(xs)+f[hi:]
    return source[:a]+f+source[b:]
for name,s in [('baseline',source),('unroll2',variant(False)),('pipeline2',variant(True))]:
    p=root/(name+'.c');p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),p)
