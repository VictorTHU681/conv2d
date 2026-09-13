#!/usr/bin/env python3
"""Retain next iteration's even-plane vectors loaded by the second FMLA step."""
from pathlib import Path
import hashlib

def e(s):return '        "'+s+'\\n\\t"\n'
for base,out in [('baseline','k9reuse'),('k9both','k9reuseboth')]:
    s=Path('build/v56/'+base+'.c').read_text()
    a=s.index('static __attribute__((noinline)) void k8f(')
    b=s.index('\n}\n',a)+3
    f=s[a:b]
    lo=f.index(e('2:'))
    hi=f.index(e('ld1w {z8.s}, p0/z, [x2]'),lo)
    head=f[lo:hi]
    pre=[]
    for i in range(4):
        instr=f'ld1w {{z{2*i}.s}}, p0/z, [x16, #{i}, mul vl]'
        old=e(instr)
        if i==0 and old not in head:old=e('ld1w {z0.s}, p0/z, [x16]')
        assert head.count(old)==1
        head=head.replace(old,'')
        pre.append(instr)
    f=f[:lo]+''.join(map(e,pre))+head+f[hi:]
    # Split version repeats a separate padded pair. Keep those one-off loads;
    # only the recurrent even-plane main-loop loads are removed.
    p=Path('build/v56/'+out+'.c');p.write_text(s[:a]+f+s[b:])
    print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
