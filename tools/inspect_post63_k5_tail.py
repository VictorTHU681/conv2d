#!/usr/bin/env python3
"""Report whether non-K5 instructions and linked addresses stay identical."""
from pathlib import Path
import hashlib,re,argparse
parser=argparse.ArgumentParser()
parser.add_argument("--root",type=Path,default=Path("build/post63/k5-tail"))
parser.add_argument("--variants",default="guard,unroll")
args=parser.parse_args()
root=args.root
def read(v):
    raw=(root/(v+'.dis')).read_bytes()
    print(v,'disassembly SHA256',hashlib.sha256(raw).hexdigest())
    rows={};symbol=None
    for line in raw.decode().splitlines():
        m=re.match(r'^[0-9a-f]+ <([^>]+)>:$',line)
        if m:symbol=m[1]
        m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',line)
        if m:rows[int(m[1],16)]=(symbol,m[2],re.sub(r'\s+',' ',m[3]).strip())
    assert len(rows)>10000 and any(v[0]=='k5' for v in rows.values())
    return rows
base=read('baseline')
for name in args.variants.split(','):
    rows=read(name)
    outer={a:v for a,v in rows.items() if v[0]!='k5'}
    base_outer={a:v for a,v in base.items() if v[0]!='k5'}
    same=outer==base_outer
    print(f'{name}: non-K5 address/opcode/operand identity={same}; total instructions {len(rows)} vs baseline {len(base)}.')
    def arithmetic_output(table):
        return {a:v for a,v in table.items() if v[0]=='k5' and
                (re.search(r'\bza[0-9]',v[2]) or v[2].split()[0] in ['fmopa','st3w'])}
    critical=arithmetic_output(base)
    assert critical and any('fmopa' in v[2] for v in critical.values())
    print(f'{name}: K5 ZA arithmetic/state/output instruction identity={arithmetic_output(rows)==critical}; {len(critical)} baseline positions.')
    if same:
        changes=[a for a in base.keys()&rows.keys() if base[a]!=rows[a]]
        assert all(base[a][0]==rows[a][0]=='k5' for a in changes)
        print(f'{len(changes)} common-address changes are exclusively inside K5; this is not a pure instruction permutation.')
    else:
        changed={base.get(a,rows.get(a))[0] for a in base.keys()|rows.keys() if base.get(a)!=rows.get(a)}
        print('Symbols containing moved/changed instructions:',', '.join(sorted(changed)))
print('This records final linked instruction identity, not a correctness proof. Timings of non-K5 shapes are retained without attributing them to K5 copy work.')
