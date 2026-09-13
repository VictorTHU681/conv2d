#!/usr/bin/env python3
"""Audit linked F3 full blocks, overlap/remainder steps and branch targets."""
from pathlib import Path
import re,hashlib,difflib
root=Path('build/post64/pairf3-unroll');out=Path('results/post64/pairf3-unroll')
def read(name):
    p=root/f'official_{name}.dis'; rows=[]; owner=''
    for line in p.read_text().splitlines():
        m=re.match(r'^[0-9a-f]+ <([^>]+)>:$',line)
        if m:owner=m[1]
        m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',line)
        if m and owner=='roll_worker':
            t=re.sub(r'\s+',' ',m[3].split('//')[0]).strip()
            t=re.sub(r'#0x([0-9a-f]+)',lambda x:'#'+str(int(x[1],16)),t)
            rows.append((int(m[1],16),t))
    print(name,'disassembly SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
    assert rows;return rows
b,c=[read(n) for n in ['baseline','u4']]
def steps(rows):
    return [i-15 for i,(_,t) in enumerate(rows) if t=='add x13, x13, #16' and rows[i-1][1]=='fmla z15.s, z1.s, z4.s[2]']
bs=steps(b);cs=steps(c);assert len(bs)==len(cs)==2
step=[t for _,t in b[bs[0]:bs[0]+19]]
assert step[:5]==['ld1w {z0.s}, p0/z, [x16]','ld1w {z1.s}, p0/z, [x16, #1, mul vl]','ld1w {z2.s}, p0/z, [x2]','ld1w {z3.s}, p0/z, [x3]','ld1rqw {z4.s}, p0/z, [x13]']
assert step[-4:]==['add x13, x13, #16','add x16, x16, #4','add x2, x2, #64','add x3, x3, #64']
for rows,starts in [(b,bs),(c,cs)]:
    for i in starts:assert [t for _,t in rows[i:i+19]]==step
ks=[i for i,(_,t) in enumerate(c) if t=='lsr x12, x15, #2'];assert len(ks)==1
k=ks[0];assert c[k+1][1]=='and x15, x15, #3'
a=k+3
while c[a][1]=='nop':a+=1
expected=[]
for q in range(4):
    core=step[:15].copy()
    if q:
        for i,reg in [(2,'x2'),(3,'x3')]:core[i]=core[i].replace(f'[{reg}]',f'[{reg}, #{q}, mul vl]')
        core[4]=core[4].replace('[x13]',f'[x13, #{16*q}]')
    expected+=core+['add x16, x16, #4']
expected+=['add x13, x13, #64','add x2, x2, #256','add x3, x3, #256','subs x12, x12, #1']
assert [t for _,t in c[a:a+len(expected)]]==expected
n=a+len(expected)
assert c[n][1].startswith(f'b.ne {c[a][0]:x} ')
assert c[k+2][1].startswith(f'cbz x12, {c[n+1][0]:x} ')
t=n+2;assert t==cs[1]
assert c[n+1][1].startswith(f'cbz x15, {c[t+21][0]:x} ')
assert c[t+19][1]=='subs x15, x15, #1'
assert c[t+20][1].startswith(f'b.ne {c[t][0]:x} ')
assert c[t+21][1]=='cmp x2, x5' # exact old row-wrap entry
# Removing just the added unrolled block leaves original worker arithmetic order.
ops=lambda rows:[t for _,t in rows if t.startswith(('fmopa ','fmla '))]
assert ops(c[:a]+c[n+1:])==ops(b)
s,v=[(root/(name+'.c')).read_text() for name in ['baseline','u4']]
x=s.index('static void k16pairf3(');y=s.index('#define SINGLEF2_STEP',x)
assert s[:x]==v[:x] and s[y:]==v[v.index('#define SINGLEF2_STEP',x):]
out.joinpath('source.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile='baseline.c',tofile='u4.c')))
print('PASS: overlap and remainder each preserve the original 19-instruction F3 step; full block has four ordered copies of five loads/four FMOPA/six FMLA with exact offsets.')
print('PASS: grouped coefficient cursor updates, four input updates, block and remainder backedges, zero-block and zero-remainder exits match intended targets.')
print('PASS: deleting the four added full-block arithmetic copies leaves the original worker arithmetic sequence; source outside k16pairf3 byte-identical.')
print(f'Full loop entry 0x{c[a][0]:x}, {len(expected)+1} instructions vs original 84 per four steps; setup/remainder excluded. Original suffix entry 0x{b[bs[1]][0]:x}.')
print('Linked addresses move; no claim of non-target machine-code identity or proof of all dynamic accesses.')
