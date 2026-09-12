#!/usr/bin/env python3
"""Separate packing time from worker time using the actual timer frequency."""
from pathlib import Path
from gen_v54 import phase_profile
import hashlib
for v in ['baseline','sharekf','veckf','sharevec']:
    s=phase_profile(Path('build/v57/'+v+'.c').read_text())
    a=s.index('    fprintf(stderr, "[v54-phase]')
    b=s.index('    if (g_roll_diag)',a)
    part=s[a:b].replace('[v54-phase]','[v57-phase]')
    part=part.replace('pksum/(100.0*nth)','pksum*(1e6/(double)cyc_hz())/nth')
    part=part.replace('/100.0','*(1e6/(double)cyc_hz())')
    s=s[:a]+part+s[b:]
    p=Path('build/v57/'+v+'_phase.c');p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),p)
