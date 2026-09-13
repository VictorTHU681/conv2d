#!/usr/bin/env python3
"""One-binary K5 plane-prefix controls on immutable upstream v61."""
from pathlib import Path
import hashlib
import subprocess

root = Path('build/post61/k5-copy-layout')
root.mkdir(parents=True, exist_ok=True)
source = subprocess.check_output(['git', 'show', 'b3140af:conv2d.c'], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == '2c4065478f8d40c194c996ede4fcdbd65f80c0a1c5e9b057b32889035d788ada'
old = 'static void read_knobs(void)'
new = 'static int g_k5_copy_mode;\n' + old
assert source.count(old) == 1
s = source.replace(old, new)
old = '    if (g_knobs.inited) return;'
new = old + '\n    g_k5_copy_mode = env_int("CONV_K5_COPY", 0);'
assert s.count(old) == 1
s = s.replace(old, new)
a = s.index('static __attribute__((noinline)) void k5(')
b = s.index('\n}\n', a) + 3
body = s[a:b]
old_sh = '    const long sh = ((uintptr_t)P->in_row >> 2) & 15;'
new_sh = '''    const long sh = g_k5_copy_mode == 1 ? 0 :
                    g_k5_copy_mode == 2 ? (3 - (P->KW + 191) % 3) % 3 :
                    ((uintptr_t)P->in_row >> 2) & 15;'''
assert body.count(old_sh) == 1
updated = body.replace(old_sh, new_sh)
assert updated.split('    asm volatile(')[1] == body.split('    asm volatile(')[1]
s = s[:a] + updated + s[b:]
reverse = s.replace(new_sh, old_sh).replace(new, old).replace('static int g_k5_copy_mode;\n', '')
assert reverse == source
(root/'candidate.c').write_text(s)
(root/'fbench.c').write_bytes(subprocess.check_output(['git', 'show', '8b6b295:tools/fbench.c']))
assert hashlib.sha256((root/'fbench.c').read_bytes()).hexdigest() == 'e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
out = Path('results/post61/k5-copy-layout')
out.mkdir(parents=True, exist_ok=True)
files = [root/'candidate.c', root/'fbench.c']
manifest = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files)
(out/'sources.sha256').write_text(manifest)
print(manifest, end='')
print('Only read-once experiment knob and K5 prefix selection differ; entire inline assembly and remaining source reverse to v61 exactly.')
