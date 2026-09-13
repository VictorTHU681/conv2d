#!/usr/bin/env python3
"""Probe the new F4 steps=64 gate across the entire K5 residual family."""
from pathlib import Path
import hashlib
root=Path('build/v56/experiments/k5-layout')
s=Path('tools/test_v56_k5_triplet.c').read_text()
assert s.count('int main(void) {')==1
s=s.replace('int main(void) {','static int extended_main_unused(void) {')
s+='''
int main(void) {
    int ok=1,cases=0;
    for(int kh=41;kh<=249;kh+=16) for(int kw=63;kw<=65;kw++) {
        for(int shift=0;shift<16;shift++) {
            ok &= aligned_case(kh,kw,192+shift%3,shift,0);cases++;
        }
        for(int ow=192;ow<=193;ow++) {
            ok &= aligned_case(kh,kw,ow,0,1);cases++;
        }
    }
    unsigned long calls,outside;
    conv_audit_report(&calls,&outside);ok &= calls>0 && outside==0;
    printf("K5_GATE_INPUT_AUDIT calls=%lu outside=%lu\\n",calls,outside);
    printf("K5_GATE %s cases=%d\\n",ok?"PASS":"FAIL",cases);
    return ok?0:1;
}
'''
p=root/'gate.c';p.write_text(s);print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
