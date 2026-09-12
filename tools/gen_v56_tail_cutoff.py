#!/usr/bin/env python3
"""End guided growth globally before the last few pieces dominate completion."""
from pathlib import Path
import hashlib
import subprocess

root=Path('build/v56/experiments/tail-cutoff');root.mkdir(parents=True,exist_ok=True)
base=subprocess.check_output(['git','show','8629457:conv2d.c'],text=True)
guided=Path('build/v56/experiments/guided-chunks/grow2.c').read_text()
assert hashlib.sha256(base.encode()).hexdigest()=='1d3f5071d51cd4f8c88720b8d4fa91983515ffd83bdeb4983377a991df2b871a'
assert hashlib.sha256(guided.encode()).hexdigest()=='70022f3be821f95e08cd80a56fd4d5d9aaa9652b4d9b70a9978fba1f98f34e38'
variants={'baseline':base,'guided':guided}
for factor in [2,4]:
    s=guided
    def once(old,new):
        global s
        assert s.count(old)==1,old
        s=s.replace(old,new)
    once('static int g_roll_guided;', '''static int g_roll_guided;
static padded_u64 g_roll_unfinished;
static int g_roll_cutoff;''')
    once('if (g_roll_guided && remaining > 4 * step)',
         'if (g_roll_guided && __atomic_load_n(&g_roll_unfinished.v, __ATOMIC_RELAXED) > (uint64_t)g_roll_cutoff && remaining > 4 * step)')
    once('    g_roll_guided = step_default == 2 && getenv("CONV_ROLL_STEP") == NULL;',
         '    g_roll_guided = step_default == 2 && getenv("CONV_ROLL_STEP") == NULL;\n'
         f'    g_roll_cutoff = {factor} * nth;\n'
         '    __atomic_store_n(&g_roll_unfinished.v, (uint64_t)g_rp.npieces, __ATOMIC_RELAXED);')
    once('        __atomic_store_n(&P->ready[pi].v, (uint64_t)(off + rows), __ATOMIC_RELEASE);',
         '        __atomic_store_n(&P->ready[pi].v, (uint64_t)(off + rows), __ATOMIC_RELEASE);\n'
         '        if (g_roll_guided && off + rows == total)\n'
         '            __atomic_sub_fetch(&g_roll_unfinished.v, 1, __ATOMIC_RELAXED);')
    # An unchanged helper is used by dependency checking and execution. The
    # unfinished count only decreases within a call, so a later worker query
    # cannot enlarge the range whose dependencies were already checked.
    for sig in ['static void roll_prepare(', 'static void roll_link_output_dependencies(',
                'static inline void carry_store_za(', 'static inline void carry_load_za(']:
        def body(t):
            a=t.index(sig);return t[a:t.index('\n}\n',a)+3]
        assert body(s)==body(guided),sig
    variants[f'cut{factor}']=s
for name,s in variants.items():
    p=root/f'{name}.c';p.write_text(s);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
p=root/'fbench.c';p.write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
assert hashlib.sha256(p.read_bytes()).hexdigest()=='e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
