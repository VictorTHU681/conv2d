#!/usr/bin/env python3
"""K9 scheduling controls, generated from immutable validated v55 source."""
from pathlib import Path
import subprocess, hashlib

BASE='0a39770'
source=subprocess.check_output(['git','show',BASE+':conv2d.c'],text=True)
root=Path('build/v56');root.mkdir(parents=True,exist_ok=True)
def emit(xs):
    return ''.join('        "'+x+'\\n\\t"\n' for x in xs)

def variant(weave=False, split=False):
    lo=source.index('static __attribute__((noinline)) void k8f(')
    hi=source.index('\n}\n',lo)+3
    f=source[lo:hi]
    a=f.index(emit(['2:']))
    b=f.index(emit(['ldr x21, [%[A], #208]']),a)
    def pair(tail=False):
        xs=[]
        for i in range(4):
            xs += [f'ld1w {{z{2*i}.s}}, p0/z, [x16, #{i}, mul vl]',
                   f'ld1w {{z{2*i+1}.s}}, p0/z, [x25, #{i}, mul vl]']
        xs += ['ld1w {z8.s}, p0/z, [x2]', 'ld1w {z9.s}, p0/z, [x2, #1, mul vl]']
        # Main loop has two actual coefficients. The single tail pair has
        # either one real coefficient (odd KW) or none (even KW).
        for half in range(2):
            do_fma=not (split and tail and half==1)
            guarded=not split or (tail and half==0)
            label=82+half
            opas=[f'fmopa za{i}.s, p0/m, p0/m, z{2*i+half}.s, z{8+half}.s' for i in range(4)]
            setup=[]
            if guarded: setup += [f'cbz x12, {label}f']
            setup += ['ld1rw {z24.s}, p0/z, [x13]', 'add x13, x13, #4']
            if guarded: setup += ['sub x12, x12, #1']
            if half:
                setup += ['add x21, x16, #4']+[f'ld1w {{z{2*i}.s}}, p0/z, [x21, #{i}, mul vl]' for i in range(4)]
            fmas=[f'fmla z{16+i}.s, p0/m, z{i if half==0 else i+1 if i%2==0 else i-1}.s, z24.s' for i in range(8)]
            # Guarded tail remains grouped so the branch skips only FMLA.
            if weave and do_fma and not guarded:
                xs+=setup
                for i in range(4): xs += [opas[i]]+fmas[2*i:2*i+2]
            elif weave and do_fma and guarded:
                # Duplicate the four OPA instructions on the no-FMA path.
                xs += setup
                for i in range(4): xs += [opas[i]]+fmas[2*i:2*i+2]
                xs += [f'b {label+10}f', f'{label}:']+opas+[f'{label+10}:']
            else:
                xs+=opas
                if do_fma:
                    xs+=setup+fmas
                    if guarded: xs+=[f'{label}:']
        xs+=['add x16, x16, #4','add x25, x25, #4','add x2, x2, #128']
        return xs
    body=['2:']+pair()+['subs x15, x15, #1','b.ne 2b']
    if split:
        # steps always contains one padded pair beyond floor(KW/2).
        body+=['ldr x12, [%[A], #264]', 'and x12, x12, #1']+pair(tail=True)
        f=f.replace('    A.T = (int64_t)P->kend; A.nlines = P->cf0; A.kw4 = P->KW;',
                    '    A.T = (int64_t)P->kend; A.nlines = P->cf0; A.kw4 = P->KW; A.it = P->KW / 2;')
        # Re-find anchors after the C argument initialization changed.
        a=f.index(emit(['2:'])); b=f.index(emit(['ldr x21, [%[A], #208]']),a)
    f=f[:a]+emit(body)+f[b:]
    return source[:lo]+f+source[hi:]

variants={'baseline':source,'k9weave':variant(weave=True),
          'k9split':variant(split=True),'k9both':variant(weave=True,split=True)}
for name,content in variants.items():
    p=root/(name+'.c');p.write_text(content)
    print(hashlib.sha256(content.encode()).hexdigest(),p)
