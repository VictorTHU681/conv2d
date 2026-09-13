#!/usr/bin/env python3
"""Check actual F3 loads/FMA/strides; avoid claiming unchanged linked layout."""
from pathlib import Path
import re,hashlib,difflib
root=Path('build/post64/pairf3-compact')
out=Path('results/post64/pairf3-compact')
def read(name):
    p=root/f'official_{name}.dis'; rows=[]; sym=''
    for line in p.read_text().splitlines():
        m=re.match(r'^[0-9a-f]+ <([^>]+)>:$',line)
        if m: sym=m[1]
        m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',line)
        if m and sym=='roll_worker':
            rows.append((int(m[1],16),re.sub(r'\s+',' ',m[3].split('//')[0]).strip()))
    assert rows
    print(name,'disassembly SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
    return rows
b,c=[read(n) for n in ['baseline','compact']]
def blocks(rows,stride):
    starts=[i-15 for i,(_,t) in enumerate(rows) if t==f'add x13, x13, #{stride}' and rows[i-1][1]=='fmla z15.s, z1.s, z4.s[2]']
    assert len(starts)==2
    seqs=[]
    for i in starts:
        seq=[t for _,t in rows[i:i+19]]
        assert seq[:5]==['ld1w {z0.s}, p0/z, [x16]','ld1w {z1.s}, p0/z, [x16, #1, mul vl]',
                           'ld1w {z2.s}, p0/z, [x2]','ld1w {z3.s}, p0/z, [x3]','ld1rqw {z4.s}, p0/z, [x13]']
        assert sum(t.startswith('fmopa ') for t in seq)==4
        assert sum(t.startswith('fmla ') for t in seq)==6
        assert seq[-3:]==['add x16, x16, #0x4','add x2, x2, #0x40','add x3, x3, #0x40']
        seqs.append(seq)
    assert seqs[0]==seqs[1]
    return starts,seqs
bs,bseq=blocks(b,'0x10');cs,cseq=blocks(c,'0xc')
assert [t.replace('#0x10','#0xc') if i==15 else t for i,t in enumerate(bseq[0])]==cseq[0]
i=cs[1]+19
assert c[i][1]=='subs x15, x15, #0x1'
assert c[i+1][1].startswith('b.ne ')
assert int(c[i+1][1].split()[1],16)==c[cs[1]][0]
assert c[i+2][1]=='add x13, x13, #0x4'
assert [t for _,t in c[i+3:i+7]]==['cmp x2, x5','csel x2, x4, x2, eq','cmp x3, x5','csel x3, x4, x3, eq']
assert [t for _,t in c[i+7:i+11]]==['ldr x24, [x18, #208]','cmp x13, x24','ldr x24, [x18, #192]','csel x13, x24, x13, eq']
# Full worker arithmetic order/operands, independent of changed instruction addresses.
ops=lambda rows:[t for _,t in rows if t.startswith(('fmopa ','fmla '))]
assert ops(b)==ops(c)
s,t=[(root/(n+'.c')).read_text() for n in ['baseline','compact']]
start='#define PAIRF4_STEP';end='#define PAIRF3_STEP'
assert s[s.index(start):s.index(end)]==t[t.index(start):t.index(end)]
out.joinpath('source.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='baseline.c',tofile='compact.c')))
print('PASS: two actual F3 compute blocks preserve five loads, four FMOPA, six FMLA and other cursor updates; only step cursor stride changes 16 -> 12 bytes.')
print('PASS: final F3 loop backedge returns to its first load; exit skips four-byte private row padding before existing coefficient-table wrap.')
print(f'PASS: all {len(ops(b))} worker FMOPA/FMLA operands and order identical; F4 macro/function source byte-identical.')
print('Linked addresses and compiler-generated packing/preparation code change. This is not an all-instruction identity proof or a dynamic ownership proof.')
