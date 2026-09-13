#!/usr/bin/env python3
"""Generate fixed K5 prefix policies, without a runtime experiment knob."""
from pathlib import Path
import hashlib
import subprocess

root = Path('build/post61/k5-copy-fixed')
root.mkdir(parents=True, exist_ok=True)
source = subprocess.check_output(['git', 'show', 'b3140af:conv2d.c'], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == '2c4065478f8d40c194c996ede4fcdbd65f80c0a1c5e9b057b32889035d788ada'
a = source.index('static __attribute__((noinline)) void k5(')
b = source.index('\n}\n', a)+3
body = source[a:b]
old = '    const long sh = ((uintptr_t)P->in_row >> 2) & 15;'
assert body.count(old) == 1
for name, expr in [('baseline', '((uintptr_t)P->in_row >> 2) & 15'),
                   ('exact', '0'), ('triples', '(3 - (P->KW + 191) % 3) % 3')]:
    new = '    const long sh = ' + expr + ';'
    changed = body.replace(old, new)
    assert changed.replace(new, old) == body
    assert changed.split('    asm volatile(')[1] == body.split('    asm volatile(')[1]
    (root/(name+'.c')).write_text(source[:a]+changed+source[b:])
(root/'bench_conv.c').write_bytes(subprocess.check_output(['git', 'show', 'd2b65c4:bench_conv.c']))
assert hashlib.sha256((root/'bench_conv.c').read_bytes()).hexdigest() == '2548861ae7e29826e454b4c0b098d682f7f04996222e664cd1ea9bc92dd2e927'
out = Path('results/post61/k5-copy-fixed')
out.mkdir(parents=True, exist_ok=True)
files = [root/(name+'.c') for name in ['baseline', 'exact', 'triples', 'bench_conv']]
manifest = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files)
(out/'sources.sha256').write_text(manifest)
print(manifest, end='')
