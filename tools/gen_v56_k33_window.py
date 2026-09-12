#!/usr/bin/env python3
"""Bounded K33 register-window controls on accepted integrated 54dc05d."""
from pathlib import Path
import hashlib
import re
import subprocess

source=subprocess.check_output(['git','show','54dc05d:conv2d.c'],text=True)
assert hashlib.sha256(source.encode()).hexdigest()=='695c449ccdc0b234ae16812a49b26afc7a7d0153d5d0b33983c7b3a281f3530b'
def macro(name):
    a=source.index('#define '+name);text=source[a:].splitlines()[1:];out=[]
    for line in text:
        continuation=line.endswith('\\')
        out.append(line[:-1].rstrip()+'\n' if continuation else line+'\n')
        if not continuation:break
    return ''.join(out)
body=macro('PAIRF_STEP')
assert body.count('ld1w')==4 and body.count('fmopa')==4 and body.count('fmla')==2
ops=body.splitlines(keepends=True)
assert len(ops)==15
math=''.join(ops[2:]).replace('        "add x16, x16, #4\\n\\t"\n','')
assert 'add x16' not in math
loop=macro('OVL_LOOP(STEP)').replace('        STEP\n',body)
start=loop.index('        "2:\\n\\t"\n')
prefix=loop[:start]
tail=loop[start:]
assert tail.count('subs x15')==1 and tail.count('fmopa')==4
def lines(ops):return ''.join('        "'+op+'\\n\\t"\n' for op in ops)
def make(unroll=0,kind='outline'):
    a=source.index('static void k16pairf(');b=source.index('\n}\n',a)+3
    f=source[a:b]
    f=f.replace('static void k16pairf(', 'static __attribute__((noinline, aligned(128))) void k16pairf(')
    if unroll:
        code=lines([f'cmp x15, #{unroll}','b.lo 62f','61:'])
        reuse=kind!='unroll'
        if reuse:
            code+=lines(['ld1w {z12.s}, p0/z, [x16]','ld1w {z13.s}, p0/z, [x16, #1, mul vl]','ld1w {z14.s}, p1/z, [x16, #2, mul vl]'])
        for j in range(unroll):
            if not reuse:code+=body
            elif j==0:
                code+=re.sub(r'\bz([01])\.s',lambda m:'z'+str(12+int(m[1]))+'.s',math)
            elif kind=='ext':
                code+=lines(['mov z0.d, z12.d',f'ext z0.b, z0.b, z13.b, #{4*j}',
                             'mov z1.d, z13.d',f'ext z1.b, z1.b, z14.b, #{4*j}'])+math
            else:
                index=15+j
                code+=lines([f'tbl z0.b, {{z12.b, z13.b}}, z{index}.b',
                             f'tbl z1.b, {{z13.b, z14.b}}, z{index}.b'])+math
        if reuse:code+=lines([f'add x16, x16, #{4*unroll}'])
        code+=lines([f'sub x15, x15, #{unroll}',f'cmp x15, #{unroll}','b.hs 61b','62:','cbz x15, 63f'])
        code+=tail+lines(['63:'])
        assert f.count('        OVL_LOOP(PAIRF_STEP)\n')==1
        f=f.replace('        OVL_LOOP(PAIRF_STEP)\n',prefix+code)
        if reuse:
            setup=lines([f'mov x12, #{unroll-1}','whilelo p1.s, xzr, x12'])
            clobbers=['z12','z13','z14','p1']
            if kind=='tbl':
                for j in range(1,unroll):
                    reg=15+j
                    setup+=lines([f'index z{reg}.b, #0, #1',f'add z{reg}.b, z{reg}.b, #{4*j}'])
                    clobbers.append('z'+str(reg))
            label='        "47:\\n\\t"\n'
            assert f.count(label)==1
            f=f.replace(label,label+setup)
            f=f.replace(': XCLOB, "z0",', ': XCLOB, '+', '.join('"'+c+'"' for c in clobbers)+', "z0",')
    s=source[:a]+f+source[b:]
    assert s.count('static void roll_worker(')==1
    return s.replace('static void roll_worker(', 'static __attribute__((aligned(128))) void roll_worker(')

root=Path('build/v56/experiments/k33-window');root.mkdir(parents=True,exist_ok=True)
variants={'baseline':source,'outline':make(),'unroll4':make(4,'unroll'),
          'ext4':make(4,'ext'),'tbl4':make(4,'tbl'),'tbl8':make(8,'tbl')}
for name,s in variants.items():
    p=root/(name+'.c');p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),p)
