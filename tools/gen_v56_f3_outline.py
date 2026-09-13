#!/usr/bin/env python3
"""Matched F3 outlining controls for the phase-setup regression."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/v56/experiments/f3-outline');root.mkdir(parents=True,exist_ok=True)
base=Path('build/v56/experiments/chunk-setup/baseline.c').read_text()
phase=Path('build/v56/experiments/chunk-setup/phase.c').read_text()
assert hashlib.sha256(base.encode()).hexdigest()=='bb82ce3b4826514e9ce6f729ef017a23d5aa08d2396f5d0975a512e39da76819'
assert hashlib.sha256(phase.encode()).hexdigest()=='0bfdf223a3f184c5d91f9435a1bde509df7846f428401d2fcd0df8f72ce657db'
for name,s,outline in [('baseline',base,False),('phase',phase,False),('baseline_out',base,True),('phase_out',phase,True)]:
    if outline:
        old='static void k16pairf3(const kp_t* P)';assert s.count(old)==1
        s=s.replace(old,'__attribute__((noinline)) '+old)
    p=root/(name+'.c');p.write_text(s);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
p=root/'fbench.c';p.write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']));print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
