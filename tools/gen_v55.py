#!/usr/bin/env python3
"""Local-only v55 experiments on v54. Do not push without user approval."""
from pathlib import Path
import hashlib
import subprocess
from v55_shift import shifted
from v55_schedule import interleaved
from v55_k4_io import k4_io
from v55_orientation import horizontal
from v55_overlap import overlap
from v55_cache import non_temporal_copy
from v55_nine import nine
from v55_nine_planes import planar_nine
from v55_nine_select import selected_nine
from gen_v54 import phase_profile

BASE = 'be7b462'

def spill(source, mode):
    a=source.index('static inline void carry_store_za(')
    b=source.index('// Each strip publishes progress', a)
    functions=[]
    for load in (False, True):
        ins='ldr' if load else 'str'
        name='load' if load else 'store'
        code=['mov w12, #0']
        if mode=='via_z': code+=['ptrue p0.b']
        code+=['49:']
        count=4
        for j in range(count):
            if mode=='via_z':
                if load: code += [f'ld1b {{z{j}.b}}, p0/z, [%[p]]',f'mova za0h.b[w12, 0], p0/m, z{j}.b']
                else: code += [f'mova z{j}.b, p0/m, za0h.b[w12, 0]',f'st1b {{z{j}.b}}, p0, [%[p]]']
                code+=['add w12, w12, #1','add %[p], %[p], #64']
            else:
                addr='[%[p]]' if j==0 else f'[%[p], #{j}, mul vl]'
                code += [f'{ins} za[w12, {j}], {addr}']
        if mode!='via_z': code+=['add w12, w12, #4','add %[p], %[p], #256']
        code += ['cmp w12, #64', 'b.lo 49b']
        asm='\n'.join('                 "'+x+'\\n\\t"' for x in code)
        clobber='"x12", "memory", "cc"'+(', "z0", "z1", "z2", "z3", "p0"' if mode=='via_z' else '')
        functions.append(f'''static inline void carry_{name}_za({'const ' if load else ''}float* p)
{{
    asm volatile(
{asm}
                 : [p] "+r"(p) : : {clobber});
}}
''')
    return source[:a]+'\n'.join(functions)+source[b:]

def direct(source, level):
    code=['ldr x12, [%[A], #240]', 'add x16, x0, x12', 'add x21, x0, x26',
          'ldr x12, [%[A], #168]', 'cbz x12, 7f', '3:',
          f'prfm pldl{level}keep, [x21]', 'add x21, x21, #64', 'subs x12, x12, #1',
          'b.ne 3b', '7:', f'prfm pldl{level}keep, [x21]']
    macro='#define ROW_HEAD_DIRECT \\\n'+' \\\n'.join('        "'+x+'\\n\\t"' for x in code)+'\n\n'
    pos=source.index('// ---------------- 16×1 对：')
    source=source[:pos]+macro+source[pos:]
    # Preserve the independent K4 deinterleaving path; all other rolling kernels
    # can load their original contiguous input directly.
    source=source.replace('        ROW_HEAD_COMMON\n', '        ROW_HEAD_DIRECT\n').replace('        ROW_HEAD_COPY4\n','        ROW_HEAD_DIRECT\n')
    old='    if (ncp) roll_copy_row(P->ring, src, ncp);'
    assert source.count(old)==1
    source=source.replace(old,'    (void)ncp;')
    return source

def main():
    source=subprocess.check_output(['git','show',BASE+':conv2d.c'],text=True)
    variants={'baseline':source,'spill4':spill(source,'direct4'),'spillz':spill(source,'via_z'),
              'directl1':direct(source,1),'directl2':direct(source,2)}
    names=['k16pair','k16pairf','k16pairf3','k16single']
    variants['extall']=shifted(source,names)
    variants['extsingle']=shifted(source,['k16single'])
    variants['extpair3']=shifted(source,['k16pairf3'])
    variants['unroll2']=shifted(source,names,False)
    variants['weaveall']=interleaved(source,['k16pairf','k16pairf3','k16pairf4'])
    variants['weave3']=interleaved(source,['k16pairf3'])
    variants['weave4']=interleaved(source,['k16pairf4'])
    variants['k4cpz']=k4_io(source,copy=True)
    variants['k4evz']=k4_io(source,output=True)
    variants['k4ioz']=k4_io(source,copy=True,output=True)
    variants['phase']=phase_profile(source)
    variants['horizall']=horizontal(source)
    variants['horizk4']=horizontal(source,k4_only=True)
    names=['k16pair','k16pairf','k16pairf3','k16pairf4','k16single']
    variants['ovall']=overlap(source,names)
    variants['ovpair4']=overlap(source,['k16pairf4'])
    variants['ovsingle']=overlap(source,['k16single'])
    variants['ntall']=non_temporal_copy(source)
    variants['ntpair4']=non_temporal_copy(source,pair4_only=True)
    variants['ntspare']=non_temporal_copy(overlap(source,['k16pair','k16pairf','k16pairf3','k16single']))
    variants['nine_reload']=nine(source)
    variants['nine_ext']=nine(source,use_ext=True)
    variants['nine_plane_reload']=planar_nine(variants['nine_reload'])
    variants['nine_plane_ext']=planar_nine(variants['nine_ext'],use_ext=True)
    for name in ('nine_reload','nine_plane_reload','nine_plane_ext'):
        variants[name+'_phase']=phase_profile(variants[name])
    variants['nine_w130']=selected_nine(variants['nine_plane_reload'])
    variants['nine_w140']=selected_nine(variants['nine_plane_reload'],weight=140)
    variants['nine_outline']=selected_nine(variants['nine_plane_reload'],outline=True)
    out=Path('build/v55');out.mkdir(parents=True,exist_ok=True)
    for n,s in variants.items():
        (out/(n+'.c')).write_text(s)
        print(n,hashlib.sha256(s.encode()).hexdigest())
if __name__=='__main__': main()
