#!/usr/bin/env python3
"""Place F3 unrolled suffix in a text subsection; preserve original inline footprint."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/post64/pairf3-island');out=Path('results/post64/pairf3-island')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','138dcac:conv2d.c'],text=True)
u4=Path('build/post64/pairf3-unroll/u4.c').read_text()
assert hashlib.sha256(s.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
assert hashlib.sha256(u4.encode()).hexdigest()=='f88b3f90295fd5ad5a749016343b266535857b53d2588801f65e18e6c7f2d499'
a=s.index('static void k16pairf3(');b=s.index('#define SINGLEF2_STEP',a)
ua=u4.index('static void k16pairf3(');ub=u4.index('#define SINGLEF2_STEP',ua)
uf=u4[ua:ub]
start=uf.index('        "lsr x12, x15, #2')
end=uf.index('        WRAP_B(x2) WRAP_B(x3)',start)
compute=uf[start:end]
assert compute.endswith('        "254:\\n\\t"\n')
loop=s[s.index('#define OVL_LOOP(STEP)'):s.index('// pairf4 事件尾')]
cut=loop.rindex('        ".p2align 4\\n"')
prefix=loop[loop.index('\n')+1:cut].replace(' \\\n','\n').replace('        STEP\n','        PAIRF3_STEP\n')
line=lambda x:'        "'+x+'\\n\\t"\n'
# One branch + 20 unreachable NOPs occupy the original 21-instruction suffix.
# Subsection 1 is appended by the assembler, with an explicit branch back.
body=prefix+'        ".p2align 4\\n"\n'+line('b 601f')+line('nop')*20
body+='        ".subsection 1\\n"\n        ".p2align 4\\n"\n'+line('601:')+compute+line('b 602f')
body+='        ".previous\\n"\n'+line('602:')
fn=s[a:b];assert fn.count('        OVL_LOOP(PAIRF3_STEP)\n')==1
c=s[:a]+fn.replace('        OVL_LOOP(PAIRF3_STEP)\n',body)+s[b:]
(root/'baseline.c').write_text(s);(root/'u4.c').write_text(u4);(root/'island.c').write_text(c)
(root/'bench_conv.c').write_bytes(subprocess.check_output(['git','show','138dcac:bench_conv.c']))
files=[root/(n+'.c') for n in ['baseline','u4','island','bench_conv']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
print('Reuses the exact validated u4 computation with an entry/exit branch; original inline instruction count retained. Actual linked addresses and all branch targets still require audit.')
print((out/'sources.sha256').read_text(),end='')
