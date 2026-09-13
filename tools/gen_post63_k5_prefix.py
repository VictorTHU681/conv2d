#!/usr/bin/env python3
"""Isolate fixed zero-prefix composition with the published v62/v63 kernel."""
from pathlib import Path
import hashlib
import subprocess

root = Path('build/post63/k5-prefix')
out = Path('results/post63/k5-prefix')
root.mkdir(parents=True, exist_ok=True)
out.mkdir(parents=True, exist_ok=True)
source = subprocess.check_output(['git', 'show', 'cf42580:conv2d.c'], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == '5a423250471305054185ef31635af7b1ca61dc0133170a048383e6ff8878d7f6'
a = source.index('static __attribute__((noinline)) void k5(')
b = source.index('\n}\n', a) + 3
body = source[a:b]
old = '    const long sh = ((uintptr_t)P->in_row >> 2) & 15;'
new = '    const long sh = 0;'
assert body.count(old) == 1
changed = body.replace(old, new)
assert changed.replace(new, old) == body
assert changed.split('    asm volatile(')[1] == body.split('    asm volatile(')[1]
(root/'baseline.c').write_text(source)
(root/'exact.c').write_text(source[:a]+changed+source[b:])
legacy = subprocess.check_output(['git', 'show', 'b3140af:conv2d.c'], text=True)
a = legacy.index('static __attribute__((noinline)) void k5(')
b = legacy.index('\n}\n', a) + 3
assert legacy[a:b].count(old) == 1
legacy = legacy[:a]+legacy[a:b].replace(old, new)+legacy[b:]
assert hashlib.sha256(legacy.encode()).hexdigest() == 'ae525112d6b1b22f9508d5edb862ba923547527012e3477630ff89bc3b5d33c8'
(root/'legacy.c').write_text(legacy)
for name, rev, digest in [
    ('fbench.c','8b6b295:tools/fbench.c','e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'),
    ('bench_conv.c','d2b65c4:bench_conv.c','2548861ae7e29826e454b4c0b098d682f7f04996222e664cd1ea9bc92dd2e927')]:
    data = subprocess.check_output(['git','show',rev])
    assert hashlib.sha256(data).hexdigest() == digest
    (root/name).write_bytes(data)
files = [root/(n+'.c') for n in ['baseline','exact','legacy','fbench','bench_conv']]
manifest = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files)
(out/'sources.sha256').write_text(manifest)
print(manifest, end='')
print('Exact changes only the K5 sh declaration in v62; all assembly and remaining source reverse byte-for-byte. Legacy is the previously validated v61 exact source.')
