#!/usr/bin/env python3
"""Diagnostic: hold linked operator fixed while toggling between-timing hashes."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/post64/hash-between');out=Path('results/post64/hash-between')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
for name,path,digest in [('baseline','build/post64/k4-indexed-store/baseline.c','08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'),('all','build/post64/k4-indexed-store/all.c','d56e8e9b9b427cf1f1b1f91c40f19ffb0e88ce18b52a03d5be0878b3bce9fa1b')]:
 s=Path(path).read_bytes();assert hashlib.sha256(s).hexdigest()==digest;(root/(name+'.c')).write_bytes(s)
s=subprocess.check_output(['git','show','8b6b295:tools/fbench.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
old='    const int runs = argc > 5 ? atoi(argv[5]) : 3;'
assert s.count(old)==1;s=s.replace(old,old+'\n    const int hash_each = getenv("SCREEN_HASH_EACH") ? atoi(getenv("SCREEN_HASH_EACH")) : 1;')
old='        int rok = hash_buf(oc, obytes) == ref_hash;';assert s.count(old)==1
s=s.replace(old,'        int checked = hash_each || r == runs - 1;\n        int rok = !checked || hash_buf(oc, obytes) == ref_hash;')
old='rok ? "PASS" : "FAIL(hash)"';assert s.count(old)==1
s=s.replace(old,'!checked ? "UNCHECKED" : rok ? "PASS" : "FAIL(hash)"')
s='// Isolated diagnostic, not the official benchmark. The first validation and\n// final timed result always hash; earlier timed hashes may be omitted.\n'+s
(root/'driver.c').write_text(s)
files=[root/(n+'.c') for n in ['baseline','all','driver']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
print((out/'sources.sha256').read_text(),end='')
