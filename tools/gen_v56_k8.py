#!/usr/bin/env python3
"""Isolate two-plane input preparation for the original K8 residual kernel."""
from pathlib import Path
import subprocess, hashlib
source=subprocess.check_output(['git','show','0a39770:conv2d.c'],text=True)
def e(s): return '        "'+s+'\\n\\t"\n'
a=source.index('static __attribute__((noinline)) void k8f(')
b=source.index('\n}\n',a)+3
f=source[a:b].replace('k8f(', 'k8planes(',1)
lo=f.index(e('ldr x13, [%[A], #184]')); hi=f.index(e('81:'),lo)+len(e('81:'))
f=f[:lo]+f[hi:]
for begin,end in [('cbz x12, 82f','82:'),('cbz x12, 83f','83:')]:
    lo=f.index(e(begin));hi=f.index(e(end),lo)+len(e(end));f=f[:lo]+f[hi:]
lo=f.index(e('ldr x21, [%[A], #208]'));hi=f.index('        WRAP_B(x2) SEL_OUT',lo)
f=f[:lo]+f[hi:]
f=f.replace(e('ldr x12, [%[A], #216]')+e('cmp x27, x12')+e('b.eq 80f'),'')
lo=f.index(e('b 4f'));hi=f.index(e('4:'),lo)
f=f[:lo]+f[hi:]
lo=f.index(e('ldr x12, [%[A], #280]'));hi=f.index(e('84:'),lo)+len(e('84:'))
f=f[:lo]+f[hi:]
# Remove unused coefficient/carry setup and vector clobbers; the retained row
# copier only uses z0/z1, and matrix work uses z0..z15 plus z31 for clearing.
f=f.replace('    A.n2 = (int64_t)P->kb0; A.e2 = (int64_t)P->kbase;\n','')
f=f.replace('    A.T = (int64_t)P->kend; A.nlines = P->cf0; A.kw4 = P->KW;\n','')
f=f.replace(e('ldr x12, [%[A], #264]'),'')
for i in range(16,24): f=f.replace(f'"z{i}", ','')
f=f.replace('"z24", ','')
s=source[:b]+'\n'+f+source[b:]
s=s.replace('else if (g->kind == 8) k8(&K);','else if (g->kind == 8) k8planes(&K);')
p=Path('build/v56/k8planes.c');p.write_text(s)
print(hashlib.sha256(s.encode()).hexdigest(),p)
