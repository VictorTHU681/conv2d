#!/usr/bin/env python3
"""Check the linked short compute blocks, leftovers and branch targets."""
from pathlib import Path
import re,hashlib,argparse
parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path('build/post64/pairf4-unroll'))
parser.add_argument('--variants',default='u2,u4')
parser.add_argument('--baseline',default='baseline')
parser.add_argument('--require-outline',action='store_true')
args=parser.parse_args();root=args.root
def read(name):
    p=root/(name+'.dis');print(name,'disassembly SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
    rows=[];owner=None
    for line in p.read_text().splitlines():
        m=re.match(r'^[0-9a-f]+ <([^>]+)>:$',line)
        if m:owner=m[1]
        m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',line)
        if m:
            asm=re.sub(r'\s+',' ',m[3].split('//')[0]).strip()
            asm=re.sub(r'#0x([0-9a-f]+)',lambda x:'#'+str(int(x[1],16)),asm)
            rows.append((int(m[1],16),m[2],asm,owner))
    return rows
base=read(args.baseline)
idx=[i for i,r in enumerate(base) if r[2]=='mov x15, x7' and base[i+1][2]=='ld1w {z0.s}, p0/z, [x16]' and base[i+5][2]=='ld1rqw {z4.s}, p0/z, [x13]' and base[i+17][2]=='fmla z17.s, z1.s, z4.s[3]']
assert len(idx)==1
b=idx[0]+1;step=[r[2] for r in base[b:b+21]]
assert step[-4:]==['add x13, x13, #16','add x16, x16, #4','add x2, x2, #64','add x3, x3, #64']
for name in args.variants.split(','):
    u={'u2':2,'u4':4,'outlined_u4':4}[name]
    rows=read(name);ks=[i for i,r in enumerate(rows) if r[2]==f'lsr x15, x7, #{u.bit_length()-1}'];assert len(ks)==1
    k=ks[0];a=k+2
    assert rows[a][0]==base[b][0]
    expected=[]
    for q in range(u):
        core=step[:17].copy()
        if q:
            for i,reg in [(2,'x2'),(3,'x3')]:core[i]=core[i].replace(f'[{reg}]',f'[{reg}, #{q}, mul vl]')
            core[4]=core[4].replace('[x13]',f'[x13, #{16*q}]')
        expected+=core+['add x16, x16, #4']
    expected += [f'add x13, x13, #{16*u}',f'add x2, x2, #{64*u}',f'add x3, x3, #{64*u}','subs x15, x15, #1']
    assert [r[2] for r in rows[a:a+len(expected)]]==expected
    n=a+len(expected)
    assert rows[n][2].startswith(f'b.ne {rows[a][0]:x} ')
    assert rows[k+1][2].startswith(f'cbz x15, {rows[n+1][0]:x} ')
    assert rows[n+1][2]==f'ands x15, x7, #{u-1}'
    t=n+3
    assert [r[2] for r in rows[t:t+21]]==step
    assert rows[t+21][2]=='subs x15, x15, #1'
    assert rows[t+22][2].startswith(f'b.ne {rows[t][0]:x} ')
    assert rows[n+2][2].startswith(f'b.eq {rows[t+23][0]:x} ')
    assert rows[a][3]==base[b][3]
    if args.require_outline:
        assert rows[a][3]=='k16pairf4'
        for table in [base,rows]:
            entry=min(r[0] for r in table if r[3]=='k16pairf4')
            assert entry%128==0
            calls=[r for r in table if r[2]==f'bl {entry:x} <k16pairf4>']
            assert len(calls)==1 and calls[0][3]=='roll_worker'
            print(f'Outlined k16pairf4 entry 0x{entry:x} is 128-byte aligned; one static BL site in roll_worker at 0x{calls[0][0]:x}.')
    print(f'{name}: short compute entry 0x{rows[a][0]:x}, same as baseline, offset {rows[a][0]%128} modulo 128 (not 128-byte aligned).')
    print(f'{name}: {u} ordered copies of 4 FMOPA/8 FMLA, exact load offsets, grouped pointer updates, full-block branch and identical scalar remainder verified.')
    print(f'{name}: full block {len(expected)+1} instructions vs baseline {23*u}; setup/remainder overhead excluded.')
    print(f'{name}: linked instructions {len(rows)} vs baseline {len(base)}; code grows and following addresses may move. No non-target timing attribution from code identity.')
print('Audit checks emitted short-loop instructions/control flow; it is not a proof of all runtime memory accesses.')
