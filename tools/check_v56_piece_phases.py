#!/usr/bin/env python3
"""Compare prepared metadata against original per-chunk modular expressions."""
from pathlib import Path
import subprocess
root=Path('build/v56/experiments/piece-phases');s=(root/'cached.c').read_text()
def function(sig):
    a=s.index(sig);return s[a:s.index('\n}\n',a)+3]
rgrp=next(line.split('//')[0] for line in s.splitlines() if line.startswith('typedef struct { int kind;'))
rpiece=next(line for line in s.splitlines() if line.startswith('typedef struct { int item;'))
a=s.index('static int roll_groups_base(');b=s.index('// 滚动形态的结构性开关',a)
groups=s[a:b]
a=s.index('            long jp=pc->ja % KH');b=s.index('\n        }',a)
assign=s[a:b]
p=root/'metadata_check.c'
p.write_text('#include <assert.h>\n#include <stddef.h>\n#include <stdio.h>\n'+rgrp+'\n'+rpiece+'\n'+
    'static int nf_mode=-1;\nstatic int env_int(const char* name,int def) { (void)name;(void)def;return nf_mode; }\n'+groups+
    function('static inline long roll_phase_sub(')+'\nstatic void prepare(rpiece_t* pc,const rgrp_t* g,long KH) {\n'+assign+'\n}\n'+r'''
static long norm(long a,long kh) { return (a%kh+kh)%kh; }
int main(void) {
    assert(sizeof(rpiece_t)==32 && offsetof(rpiece_t,ja)==8 && offsetof(rpiece_t,dep_first)==24);
    const int modes[]={-1,0,3,4}; const long kws[]={3,4,399,400};
    const long widths[]={31,32,63,64,127,128,191,192,256};
    const long steps[]={1,2,4,8,16}, chunks[]={0,1,7};
    unsigned long cases=0,plans=0;
    for(int m=0;m<4;m++) { nf_mode=modes[m];
        for(long kh=16;kh<=256;kh++) for(int kw=0;kw<4;kw++) for(int w=0;w<9;w++) {
            rgrp_t G[12]={0};int ng=roll_groups_width(kh,kws[kw],G,widths[w]);plans++;
            long starts[]={0,kh-1,kh,3*kh+5,65537*kh+kh/2};
            for(int g=0;g<ng;g++) for(int st=0;st<5;st++) {
                rpiece_t pc={.item=g,.ja=starts[st]};prepare(&pc,&G[g],kh);
                for(int z=0;z<5;z++) for(int c=0;c<3;c++) {
                    long ja=pc.ja+steps[z]*chunks[c]*kh;
                    assert(pc.ya==norm(ja-G[g].s_base,kh));
                    assert(pc.yb==norm(ja-G[g].s_base-16,kh));
                    assert((pc.ya+1==kh ? 0 : pc.ya+1)==norm(ja+1-G[g].s_base,kh));
                    assert((pc.yb+1==kh ? 0 : pc.yb+1)==norm(ja+1-G[g].s_base-16,kh));
                    assert(pc.af==norm(ja-G[g].sf,kh));assert(pc.cf==norm(G[g].sf-G[g].s_base,kh));cases++;
                }
            }
        }
    }
    printf("PIECE_PHASE_EQUIVALENCE PASS cases=%lu plans=%lu piece_size=32 ja_offset=8 dep_offset=24\n",cases,plans);
}
''')
subprocess.run(['gcc','-O2','-fsanitize=address,undefined',str(p),'-o',str(root/'metadata_check')],check=True)
subprocess.run([str(root/'metadata_check')],check=True)
