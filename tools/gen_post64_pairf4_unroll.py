#!/usr/bin/env python3
"""Amortize pointer updates only in the serial short-row PAIRF4 compute loop."""
from pathlib import Path
import hashlib,re,subprocess
root=Path('build/post64/pairf4-unroll');out=Path('results/post64/pairf4-unroll')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','3f8c8c2:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='0136da05ea4658fb5792412e95baaec0e38ff299b176e5de681f228bca88da93'
start=s.index('static void k16pairf4(');end=s.index('#define PAIRF3_STEP',start)
fn=s[start:end]
old='''        "mov x15, x7\\n\\t"
        "2:\\n\\t"
        PAIRF4_STEP
        "subs x15, x15, #1\\n\\t"
        "b.ne 2b\\n\\t"
'''
assert fn.count(old)==1
step=s[s.index('#define PAIRF4_STEP'):start]
inst=re.findall(r'"([^"\n]+)\\n\\t"',step)
assert len(inst)==21
assert inst[-4:]==['add x13, x13, #16','add x16, x16, #4','add x2, x2, #64','add x3, x3, #64']
compute=inst[:17]
assert sum(x.startswith('fmopa') for x in compute)==4 and sum(x.startswith('fmla') for x in compute)==8

def line(x):return '        "'+x+'\\n\\t"\n'
for name,u in [('baseline',1),('u2',2),('u4',4)]:
    data=s
    if u>1:
        body=line(f'lsr x15, x7, #{u.bit_length()-1}')+line('cbz x15, 202f')+line('2:')
        for q in range(u):
            a=compute.copy()
            for i,reg in [(2,'x2'),(3,'x3')]:
                assert f'[{reg}]' in a[i]
                a[i]=a[i].replace(f'[{reg}]',f'[{reg}, #{q}, mul vl]')
            assert '[x13]' in a[4]
            a[4]=a[4].replace('[x13]',f'[x13, #{16*q}]')
            body+=''.join(map(line,a))+line('add x16, x16, #4')
        body+=line(f'add x13, x13, #{16*u}')+line(f'add x2, x2, #{64*u}')+line(f'add x3, x3, #{64*u}')
        body+=line('subs x15, x15, #1')+line('b.ne 2b')+line('202:')
        body+=line(f'ands x15, x7, #{u-1}')+line('b.eq 204f')+line('203:')
        body+='        PAIRF4_STEP\n'+line('subs x15, x15, #1')+line('b.ne 203b')+line('204:')
        candidate=fn.replace(old,body,1)
        # One extra setup instruction; remove one old hoisted NOP to retain
        # the existing short-loop entry address modulo 128 (verify linked code).
        pad='        ".p2align 7\\n"\n'+line('nop')*19
        assert candidate.count(pad)==1
        candidate=candidate.replace(pad,'        ".p2align 7\\n"\n'+line('nop')*18,1)
        assert candidate[candidate.index('        "172:'):]==fn[fn.index('        "172:'):]
        data=s[:start]+candidate+s[end:]
    (root/(name+'.c')).write_text(data)
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
assert hashlib.sha256((root/'fbench.c').read_bytes()).hexdigest()=='e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
files=[root/(n+'.c') for n in ['baseline','u2','u4','fbench']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
bench=subprocess.check_output(['git','show','3f8c8c2:bench_conv.c'])
assert hashlib.sha256(bench).hexdigest()=='2548861ae7e29826e454b4c0b098d682f7f04996222e664cd1ea9bc92dd2e927'
(root/'bench_conv.c').write_bytes(bench)
(out/'official_sources.sha256').write_text(''.join(f'{hashlib.sha256((root/n).read_bytes()).hexdigest()}  {root/n}\n' for n in ['baseline.c','u2.c','u4.c','bench_conv.c']))
# Model the generated addressing, exact ordered step count and end pointers.
# Fixed 64-byte SVL is already required by the production kernel.
checks=0
for u in [2,4]:
    for kw in range(1,401):
        offsets=[];x2=x3=x13=x16=0
        for block in range(kw//u):
            for q in range(u):
                offsets.append((x16,x2+64*q,x3+64*q,x13+16*q))
                x16+=4
            x2+=64*u;x3+=64*u;x13+=16*u
        for q in range(kw%u):
            offsets.append((x16,x2,x3,x13))
            x16+=4;x2+=64;x3+=64;x13+=16
        assert offsets==[(4*i,64*i,64*i,16*i) for i in range(kw)]
        assert (x16,x2,x3,x13)==(4*kw,64*kw,64*kw,16*kw)
        checks+=1
print(f'{checks} ordered-address models PASS (KW 1..400, U2/U4); no padded steps or expanded reads. Not a dynamic assembly memory proof.')
print((out/'sources.sha256').read_text(),end='')
