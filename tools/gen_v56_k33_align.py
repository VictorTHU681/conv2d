#!/usr/bin/env python3
"""Control K33 inner-loop placement without padding the repeated row path."""
from pathlib import Path
import ast,re,hashlib,subprocess
base=subprocess.check_output(['git','show','93163b4:conv2d.c'],text=True)
previous=subprocess.check_output(['git','show','72b10c2:conv2d.c'],text=True)
def align(source,power):
    a=source.index('#define ROW_HEAD_COMMON');b=source.index('#define ROW_HEAD_COPY4',a)
    lines=''.join(ast.literal_eval(x) for x in re.findall(r'"(?:[^"\\]|\\.)*"',source[a:b])).splitlines()
    instructions=[x.strip() for x in lines if x.strip() and not x.strip().endswith(':')]
    assert all(not x.startswith('.') for x in instructions)
    size=1<<power; pad=(-(len(instructions)+1)*4)%size
    a=source.index('static void k16pairf(');b=source.index('\n}\n',a)+3
    f=source[a:b];label='        "1:\\n\\t"\n';assert f.count(label)==1
    prefix=f'        ".p2align {power}\\n"\n'+'        "nop\\n\\t"\n'*(pad//4)
    return source[:a]+f.replace(label,prefix+label)+source[b:]
root=Path('build/v56/experiments/k33-align');root.mkdir(parents=True,exist_ok=True)
for name,s in [('baseline',base),('previous',previous),('align64',align(base,6)),('align128',align(base,7)),('prior128',align(previous,7))]:
    p=root/(name+'.c');p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),p)
