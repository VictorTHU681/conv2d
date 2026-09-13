#!/usr/bin/env python3
"""Unroll only the compute-only suffix of PAIRF3; original coefficient layout."""
from pathlib import Path
import hashlib,re,subprocess
root=Path('build/post64/pairf3-unroll');out=Path('results/post64/pairf3-unroll')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','138dcac:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
a=s.index('static void k16pairf3(');b=s.index('#define SINGLEF2_STEP',a)
fn=s[a:b]
step=s[s.index('#define PAIRF3_STEP'):a]
inst=re.findall(r'"([^"\n]+)\\n\\t"',step)
assert len(inst)==19
assert inst[-4:]==['add x13, x13, #16','add x16, x16, #4','add x2, x2, #64','add x3, x3, #64']
ovl=s[s.index('#define OVL_LOOP(STEP)'):s.index('// pairf4 事件尾')]
# Expand the prefix into F3 only. The shared macro and other kernels stay intact.
cut=ovl.rindex('        ".p2align 4\\n"')
prefix=ovl[ovl.index('\n')+1:cut].replace(' \\\n','\n').replace('        STEP\n','        PAIRF3_STEP\n')
assert prefix.count('        PAIRF3_STEP\n')==1 and 'OVL_TAIL' in prefix
line=lambda x:'        "'+x+'\\n\\t"\n'
body=prefix+line('lsr x12, x15, #2')+line('and x15, x15, #3')+line('cbz x12, 252f')
body+='        ".p2align 4\\n"\n'+line('251:')
for q in range(4):
    block=inst[:15].copy()
    for i,reg in [(2,'x2'),(3,'x3')]:
        block[i]=block[i].replace(f'[{reg}]',f'[{reg}, #{q}, mul vl]')
    block[4]=block[4].replace('[x13]',f'[x13, #{q*16}]')
    body+=''.join(map(line,block))+line('add x16, x16, #4')
body+=line('add x13, x13, #64')+line('add x2, x2, #256')+line('add x3, x3, #256')
body+=line('subs x12, x12, #1')+line('b.ne 251b')+line('252:')+line('cbz x15, 254f')+line('253:')
body+='        PAIRF3_STEP\n'+line('subs x15, x15, #1')+line('b.ne 253b')+line('254:')
assert fn.count('        OVL_LOOP(PAIRF3_STEP)\n')==1
candidate=fn.replace('        OVL_LOOP(PAIRF3_STEP)\n',body)
c=s[:a]+candidate+s[b:]
assert c[:a]==s[:a] and c[c.index('#define SINGLEF2_STEP',a):]==s[b:]
(root/'baseline.c').write_text(s);(root/'u4.c').write_text(c)
(root/'bench_conv.c').write_bytes(subprocess.check_output(['git','show','138dcac:bench_conv.c']))
files=[root/(n+'.c') for n in ['baseline','u4','bench_conv']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
# Include every overlap split, even the defensive zero-suffix case; real fill_args
# leaves at least one compute-only step. Verify exact ordered load addresses.
checks=0
for kw in range(1,401):
    for ovn in range(kw+1):
        x16,x2,x3,x13=4*ovn,64*ovn,64*ovn,16*ovn
        offsets=[]
        for block in range((kw-ovn)//4):
            for q in range(4):
                offsets.append((x16,x2+64*q,x3+64*q,x13+16*q));x16+=4
            x2+=256;x3+=256;x13+=64
        for _ in range((kw-ovn)%4):
            offsets.append((x16,x2,x3,x13));x16+=4;x2+=64;x3+=64;x13+=16
        assert offsets==[(4*i,64*i,64*i,16*i) for i in range(ovn,kw)]
        assert (x16,x2,x3,x13)==(4*kw,64*kw,64*kw,16*kw)
        checks+=1
print(f'{checks} ordered suffix-address models PASS; KW1..400, every overlap split including empty suffix. Real machine code and dynamic tests pending.')
print('Four compute-only steps: 84 -> 69 static instructions per full loop block, excluding setup/remainder; no speed claim.')
print((out/'sources.sha256').read_text(),end='')
