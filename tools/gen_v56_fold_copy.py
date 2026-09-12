#!/usr/bin/env python3
"""Separate three-fold grouping from input-copy and inner-loop placement."""
from pathlib import Path
import subprocess,hashlib,re,ast
source=subprocess.check_output(['git','show','72b10c2:conv2d.c'],text=True)
assert source.count('#define CONV_NF_REM7 0')==1
nf3=source.replace('#define CONV_NF_REM7 0','#define CONV_NF_REM7 3')
a=nf3.index('static void k16pairf3(');b=nf3.index('\n}\n',a)+3
f=nf3[a:b];assert f.count('ROW_HEAD_COMMON')==1
copy=nf3[:a]+f.replace('ROW_HEAD_COMMON','ROW_HEAD_COPY4')+nf3[b:]
c=copy.index('#define ROW_HEAD_COPY4');d=copy.index('static void k16pair(',c)
literals=re.findall(r'"(?:[^"\\]|\\.)*"',copy[c:d])
instructions=[x.strip() for x in ''.join(map(ast.literal_eval,literals)).splitlines() if x.strip() and not x.strip().endswith(':')]
assert all(not x.startswith('.') for x in instructions)
pad=(-(len(instructions)+1)*4)%128
f=copy[a:copy.index('\n}\n',a)+3]
old='        ".p2align 4\\n"\n';assert f.count(old)==1
f=f.replace(old,'')
label='        "1:\\n\\t"\n';assert f.count(label)==1
prefix='        ".p2align 7\\n"\n'+'        "nop\\n\\t"\n'*(pad//4)
aligned=copy[:a]+f.replace(label,prefix+label)+copy[copy.index('\n}\n',a)+3:]
root=Path('build/v56/experiments/fold-copy');root.mkdir(parents=True,exist_ok=True)
for name,s in [('baseline',source),('nf3',nf3),('f3copy',copy),('f3copy128',aligned)]:
    p=root/(name+'.c');p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),p)
