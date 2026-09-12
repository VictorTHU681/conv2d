#!/usr/bin/env python3
"""Select short continuation chunks from the actual K5 plan, not public dimensions."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/v56/experiments/k5-default');root.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','113d3d6:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='4b35b3d5af1d85c8d6cf2ddc54073c0ccc75467cdc185229e0bbd906b355f905'
(root/'baseline.c').write_text(s)
old='    g_roll_step = env_int("CONV_ROLL_STEP", 8);\n    roll_prepare(k, H, W, KH, KW, nth);'
assert s.count(old)==1
# Preparation itself must not consume the previous call's chunk setting.
a=s.index('static void roll_prepare(');b=s.index('\n}\n',a)+3
assert 'g_roll_step' not in s[a:b]
for name,step in [('short2',2),('short4',4)]:
    new='''    roll_prepare(k, H, W, KH, KW, nth);
    int step_default=8;
    for(int g=0;g<g_rp.ng;g++) if(g_rp.G[g].kind==5) { step_default=STEP; break; }
    g_roll_step = env_int("CONV_ROLL_STEP", step_default);'''.replace('STEP;',str(step)+';')
    v=s.replace(old,new)
    for sig in ['static void roll_worker(', 'static int resume_claim(', 'static void roll_link_output_dependencies(', 'static void roll_prepare(']:
        def extract(t):
            a=t.index(sig);b=t.index('\n}\n',a)+3;return t[a:b]
        assert extract(s)==extract(v),sig
    (root/(name+'.c')).write_text(v)
for name in ['baseline','short2','short4']:
    p=root/(name+'.c');print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
