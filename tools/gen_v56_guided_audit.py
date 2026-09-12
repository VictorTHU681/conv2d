#!/usr/bin/env python3
"""Count actual large/small chunks in the output-ownership diagnostic only."""
from pathlib import Path
import hashlib
import subprocess

root=Path('build/v56/experiments/guided-chunks')
subprocess.run(['python3','tools/gen_v56_output_overlap_audit.py','--root',str(root),
                '--variants','grow2,grow4'],check=True)
for name in ['grow2','grow4']:
    p=root/f'{name}_overlap.c'
    s=p.read_text()
    anchor='static void roll_worker('
    assert s.count(anchor)==1
    s=s.replace(anchor,'''static unsigned long guided_large, guided_small;
void conv_guided_audit_report(unsigned long* large,unsigned long* small) {
    *large=__atomic_load_n(&guided_large,__ATOMIC_RELAXED);
    *small=__atomic_load_n(&guided_small,__ATOMIC_RELAXED);
}
'''+anchor)
    anchor='        long rows = roll_chunk_rows(total, off, step);'
    assert s.count(anchor)==1
    s=s.replace(anchor,anchor+'''
        if(g_roll_guided) {
            if(rows>step) __atomic_fetch_add(&guided_large,1,__ATOMIC_RELAXED);
            else __atomic_fetch_add(&guided_small,1,__ATOMIC_RELAXED);
        }''')
    p.write_text(s)
    print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
