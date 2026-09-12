#!/usr/bin/env python3
"""Diagnostic-only skipped padding to isolate F3 code-position sensitivity."""
from pathlib import Path
import hashlib
src=Path('build/v56/experiments/chunk-setup/phase.c').read_text()
assert hashlib.sha256(src.encode()).hexdigest()=='0bfdf223a3f184c5d91f9435a1bde509df7846f428401d2fcd0df8f72ce657db'
root=Path('build/v56/experiments/f3-padding');root.mkdir(parents=True,exist_ok=True)
a=src.index('static void k16pairf3(');b=src.index('\n}\n',a)+3
body=src[a:b];assert '99:' not in body and body.count('    asm volatile(\n        LOAD_ARGS')==1
for name,size in [('phase',0),('p32',32),('p64',64),('p96',96)]:
    if size:
        prefix='    asm volatile(\n        "b 99f\\n\\t"\n        ".rept '+str(size//4-1)+'\\n\\t"\n        "nop\\n\\t"\n        ".endr\\n\\t"\n        "99:\\n\\t"\n        LOAD_ARGS'
        v=src[:a]+body.replace('    asm volatile(\n        LOAD_ARGS',prefix)+src[b:]
    else:v=src
    p=root/(name+'.c');p.write_text(v);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
p=root/'fbench.c';p.write_bytes(Path('build/v56/experiments/chunk-setup/fbench.c').read_bytes());print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
