#!/usr/bin/env python3
"""Test whether K9's reduced cost warrants a different initial task weight."""
from pathlib import Path
import hashlib
source=Path('build/v56/k9reuseboth.c').read_text()
assert hashlib.sha256(source.encode()).hexdigest()=='472e4bcd213c538e3cc827c6476cee8a61a528f4bb4709d475e961c175339964'
old='G->kind == 9 ? 140/100.0 :'
assert source.count(old)==1
root=Path('build/v56/balance');root.mkdir(exist_ok=True)
for name,weight in [('baseline',140),('w110',110),('w125',125)]:
    p=root/(name+'.c')
    p.write_text(source.replace(old,f'G->kind == 9 ? {weight}/100.0 :'))
    print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
