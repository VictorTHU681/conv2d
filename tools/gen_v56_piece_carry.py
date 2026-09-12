#!/usr/bin/env python3
"""Match metadata preparation and four-slice ZA carry controls."""
from pathlib import Path
import hashlib
root=Path('build/v56/experiments/piece-carry');root.mkdir(parents=True,exist_ok=True)
sources={}
for name,path,expected in [
    ('baseline','piece-phases/baseline.c','bb82ce3b4826514e9ce6f729ef017a23d5aa08d2396f5d0975a512e39da76819'),
    ('cached','piece-phases/cached.c','98190835ced6c76221fd55c3b66cbe6db4af6465a3244b9638f1e04d4e0ca2e3'),
    ('carry4','chunk-setup/carry4.c','8b4a516850cf2144d7940e68c9535320bcc78081725174b8e1d1a552dfcb03d7')]:
    t=Path('build/v56/experiments',path).read_text();assert hashlib.sha256(t.encode()).hexdigest()==expected;sources[name]=t
combo=sources['cached']
def extract(t,sig):
    a=t.index(sig);return t[a:t.index('\n}\n',a)+3]
for sig in ['static inline void carry_store_za(', 'static inline void carry_load_za(']:
    old=extract(sources['baseline'],sig);assert extract(combo,sig)==old
    combo=combo.replace(old,extract(sources['carry4'],sig))
for sig in ['static void roll_worker(', 'static void roll_prepare(', 'static int resume_claim(', 'static void roll_link_output_dependencies(']:
    assert extract(combo,sig)==extract(sources['cached'],sig),sig
sources['combined']=combo
for name,t in sources.items():
    p=root/(name+'.c');p.write_text(t);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
p=root/'fbench.c';p.write_bytes(Path('build/v56/experiments/piece-phases/fbench.c').read_bytes());print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
