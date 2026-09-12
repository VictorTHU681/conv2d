#!/usr/bin/env python3
"""Count actual large/small chunks in the output-ownership diagnostic only."""
from pathlib import Path
import hashlib
import subprocess
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path('build/v56/experiments/guided-chunks'))
parser.add_argument('--variants',default='grow2,grow4')
args=parser.parse_args();root=args.root
subprocess.run(['python3','tools/gen_v56_output_overlap_audit.py','--root',str(root),
                '--variants',args.variants],check=True)
for name in args.variants.split(','):
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
    if 'static padded_u64 g_roll_unfinished;' in s:
        anchor='    run_parallel(nth, &ctx, g_knobs.pool);\n    if (g_roll_diag)'
        assert s.count(anchor)==1
        s=s.replace(anchor,'''    run_parallel(nth, &ctx, g_knobs.pool);
    if(g_roll_guided && __atomic_load_n(&g_roll_unfinished.v,__ATOMIC_RELAXED)!=0) {
        fprintf(stderr,"GUIDED_REMAINING FAIL\\n"); abort();
    }
    if (g_roll_diag)''')
    p.write_text(s)
    print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
