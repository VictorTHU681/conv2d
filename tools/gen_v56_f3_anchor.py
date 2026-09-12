#!/usr/bin/env python3
"""Matched inline F3 layout anchors; keep phase and layout changes separable."""
from pathlib import Path
import argparse,hashlib
parser=argparse.ArgumentParser();parser.add_argument('--pad-nops',type=int,default=20);args=parser.parse_args()
assert 0<=args.pad_nops<32
root=Path('build/v56/experiments/f3-anchor');root.mkdir(parents=True,exist_ok=True)
for name,parent,anchor in [('baseline','baseline',False),('phase','phase',False),('baseline_anchor','baseline',True),('phase_anchor','phase',True)]:
    s=Path(f'build/v56/experiments/chunk-setup/{parent}.c').read_text()
    assert hashlib.sha256(s.encode()).hexdigest()=={'baseline':'bb82ce3b4826514e9ce6f729ef017a23d5aa08d2396f5d0975a512e39da76819','phase':'0bfdf223a3f184c5d91f9435a1bde509df7846f428401d2fcd0df8f72ce657db'}[parent]
    if anchor:
        a=s.index('static void k16pairf3(');b=s.index('\n}\n',a)+3;body=s[a:b]
        old='    asm volatile(\n        LOAD_ARGS';assert body.count(old)==1 and '99:' not in body
        prefix='    asm volatile(\n        "b 99f\\n\\t"\n        ".p2align 7\\n\\t"\n        ".rept '+str(args.pad_nops)+'\\n\\t"\n        "nop\\n\\t"\n        ".endr\\n\\t"\n        "99:\\n\\t"\n        LOAD_ARGS'
        s=s[:a]+body.replace(old,prefix)+s[b:]
    p=root/(name+'.c');p.write_text(s);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
p=root/'fbench.c';p.write_bytes(Path('build/v56/experiments/chunk-setup/fbench.c').read_bytes());print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
