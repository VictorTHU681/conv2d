#!/usr/bin/env python3
"""Copy only the live first-row input span; preserve alignment of later row copies."""
from pathlib import Path
import hashlib, subprocess
subprocess.run(['python3','tools/gen_v56_fold_select.py'],check=True,stdout=subprocess.DEVNULL)
prior=Path('build/v56/experiments/fold-select')
root=Path('build/v56/experiments/first-copy');root.mkdir(parents=True,exist_ok=True)
def fix(s):
    old='    const float* src = P->in_row - sh;'
    new='    const float* src = (const float*)((uintptr_t)P->in_row - (uintptr_t)sh * sizeof(float));'
    assert s.count(old)==1;s=s.replace(old,new)
    old='if (ncp) roll_copy_row(P->ring, src, ncp);'
    new='if (ncp) roll_copy_row(P->ring + sh, P->in_row, ncp - sh);'
    assert s.count(old)==1
    return s.replace(old,new)
def audit(s):
    a=s.index('static void roll_copy_row(')
    s=s[:a]+'static uintptr_t audit_input_lo, audit_input_hi;\nstatic unsigned long audit_calls, audit_overreads;\nvoid conv_audit_reset(void) { audit_calls = audit_overreads = 0; }\nunsigned long conv_audit_calls(void) { return audit_calls; }\nunsigned long conv_audit_overreads(void) { return audit_overreads; }\n'+s[a:]
    a=s.index('static void roll_copy_row(');b=s.index('{',a)+1
    s=s[:b]+'\n    __atomic_fetch_add(&audit_calls, 1, __ATOMIC_RELAXED);\n    if ((uintptr_t)src < audit_input_lo || (uintptr_t)src + (size_t)n * sizeof(float) > audit_input_hi)\n        __atomic_fetch_add(&audit_overreads, 1, __ATOMIC_RELAXED);\n'+s[b:]
    a=s.index('void conv2d(const CONVFLOAT* input,');b=s.index('{',a)+1
    return s[:b]+'\n    audit_input_lo = (uintptr_t)input;\n    audit_input_hi = audit_input_lo + (size_t)inputHeight * inputWidth * sizeof(float);\n'+s[b:]
base=(prior/'baseline.c').read_text()
variants={'baseline':base,'firstsafe':fix(base),'selectsafe':fix((prior/'select128.c').read_text())}
for name,s in variants.items():
    for suffix,content in [('',s),('_audit',audit(s))]:
        p=root/(name+suffix+'.c');p.write_text(content)
        print(hashlib.sha256(content.encode()).hexdigest(),p)
