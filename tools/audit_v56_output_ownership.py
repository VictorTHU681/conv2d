#!/usr/bin/env python3
"""Audit actual rolling grouping/claim code on the host; no SME execution claim."""
from pathlib import Path
import hashlib
import subprocess

source = subprocess.check_output(['git', 'show', '54dc05d:conv2d.c'], text=True)
root = Path('build/v56/experiments/output-ownership')
root.mkdir(parents=True, exist_ok=True)
types = source[source.index('typedef struct { int kind;'):source.index('static rplan_t g_rp;')]
groups = source[source.index('static int roll_groups_base('):source.index('// KW 在条带步数上限内')]
claim = source[source.index('static int resume_claim('):source.index('\nstatic void roll_worker(')]
# This diagnostic claims compute-ready pieces without entering SME code.
prefix = '''#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef struct { uint64_t v; } padded_u64;
static padded_u64 g_pk_gdone[12];
static int env_int(const char* name, int fallback) { (void)name; return fallback; }
'''
main = r'''
int main(void) {
    const long shapes[][4]={{4096,6144,39,39},{6144,4096,41,41},
                            {4256,6390,55,55},{6390,4256,81,81}};
    for (int si=0;si<4;si++) {
        long H=shapes[si][0],W=shapes[si][1],KH=shapes[si][2],KW=shapes[si][3];
        long OH=H-KH+1,OW=W-KW+1;
        rplan_t P={0};
        P.ng=roll_groups_width(KH,KW,P.G,OW);
        for (int g=0;g<P.ng;g++) {
            rgrp_t* G=&P.G[g];
            long count=(OW+G->width-1)/G->width;
            if (count<2 || OW%G->width==0) continue;
            long left=(count-2)*G->width,right=OW-G->width;
            long overlap=left+G->width-right;
            ritem_t items[2]={{g,left},{g,right}};
            rpiece_t pieces[2]={{0,0,OH},{1,0,OH}};
            padded_u64 ready[2]={{0},{0}};
            P.items=items; P.pieces=pieces; P.ready=ready; P.npieces=2;
            int cursor0=0,cursor1=1; long off0=-1,off1=-1;
            int a=resume_claim(&P,0,1,&cursor0,KH,&off0,0);
            int b=resume_claim(&P,1,2,&cursor1,KH,&off1,0);
            if(a!=0 || b!=1 || off0 || off1 || overlap<=0) return 2;
            printf("| %ld | %d | %ld | [%ld,%ld) | [%ld,%ld) | %ld | both busy |\n",
                   KH,G->kind,G->width,left,left+G->width,right,right+G->width,overlap);
        }
    }
    return 0;
}
'''
(root/'audit.c').write_text(prefix+types+groups+claim+main)
subprocess.run(['gcc','-O2','-Wall','-Wextra',str(root/'audit.c'),'-o',str(root/'audit')],check=True,
               stdout=subprocess.PIPE,stderr=subprocess.PIPE)
print('Source: 54dc05d, SHA-256 `'+hashlib.sha256(source.encode()).hexdigest()+'`.')
print('\nHost diagnostic uses the source grouping and resume_claim functions unchanged.')
print('Two synthetic independent pieces span the same output rows in adjacent last strips.')
print('Both can be claimed before either publishes completion. This demonstrates missing')
print('cross-item exclusion, not a measured simultaneous SME store or an incorrect result.')
print('\n| KH | Kind | Strip width | Penultimate columns | Final columns | Shared columns | Claim state |')
print('| --- | --- | ---: | --- | --- | ---: | --- |')
print(subprocess.check_output([str(root/'audit')],text=True),end='')
