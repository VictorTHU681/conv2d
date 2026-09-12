#!/usr/bin/env python3
"""Use larger early K5 chunks while retaining fine completion granularity."""
from pathlib import Path
import hashlib
import subprocess

root = Path('build/v56/experiments/guided-chunks')
root.mkdir(parents=True, exist_ok=True)
source = subprocess.check_output(['git', 'show', '8629457:conv2d.c'], text=True)
assert hashlib.sha256(source.encode()).hexdigest() == '1d3f5071d51cd4f8c88720b8d4fa91983515ffd83bdeb4983377a991df2b871a'

def extract(text, signature):
    a = text.index(signature)
    return text[a:text.index('\n}\n', a)+3]

for name, factor in [('baseline', 1), ('grow2', 2), ('grow4', 4)]:
    s = source
    if factor != 1:
        def once(old, new):
            global s
            assert s.count(old) == 1, old
            s = s.replace(old, new)
        helper = f'''static int g_roll_guided;
// Claims and execution must use the same rows, including dependency waits.
static inline long roll_chunk_rows(long total, long off, long step)
{{
    long remaining = total - off;
    long limit = step;
    if (g_roll_guided && remaining > {2*factor} * step) limit = {factor} * step;
    return remaining < limit ? remaining : limit;
}}
'''
        once('static int resume_claim(', helper + 'static int resume_claim(')
        once('long rows = total - (long)w; if (rows > step) rows = step;',
             'long rows = roll_chunk_rows(total, (long)w, step);')
        once('long rows = total - off; if (rows > step) rows = step;',
             'long rows = roll_chunk_rows(total, off, step);')
        once('    g_roll_step = env_int("CONV_ROLL_STEP", step_default);',
             '    g_roll_step = env_int("CONV_ROLL_STEP", step_default);\n'
             '    g_roll_guided = step_default == 2 && getenv("CONV_ROLL_STEP") == NULL;')
        for sig in ['static void roll_prepare(', 'static void roll_link_output_dependencies(',
                    'static inline void carry_store_za(', 'static inline void carry_load_za(',
                    'static void k16pairf4(', 'static __attribute__((noinline)) void k5(']:
            assert extract(s, sig) == extract(source, sig), (name, sig)
    p = root / f'{name}.c'
    p.write_text(s)
    print(hashlib.sha256(p.read_bytes()).hexdigest(), p)
p = root / 'fbench.c'
p.write_bytes(subprocess.check_output(['git', 'show', '8b6b295:tools/fbench.c']))
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
print(hashlib.sha256(p.read_bytes()).hexdigest(), p)
