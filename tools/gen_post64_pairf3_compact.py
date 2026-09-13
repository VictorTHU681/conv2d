#!/usr/bin/env python3
"""Compact kind-34 coefficients with a private padding word per packed row."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/post64/pairf3-compact');out=Path('results/post64/pairf3-compact')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
s=subprocess.check_output(['git','show','138dcac:conv2d.c'],text=True)
assert hashlib.sha256(s.encode()).hexdigest()=='08400a7659134bf7bee3b14df24fc919537c9fef634d1b580bf66fba0b112357'
def once(s,old,new):
 assert s.count(old)==1,(s.count(old),old[:80]);return s.replace(old,new,1)
c=s
# Only F3 moves by three coefficients; F4 retains its original four lanes.
a=c.index('#define PAIRF3_STEP');b=c.index('static void k16pairf3(',a)
part=once(c[a:b],'"add x13, x13, #16','"add x13, x13, #12');c=c[:a]+part+c[b:]
a=c.index('static void k16pairf3(');b=c.index('#define',a)
part=c[a:b]
part=once(part,'A.kw4 = P->steps * 16;', 'A.kw4 = (P->steps * 3 + 1) * 4;')
part=once(part,'        OVL_LOOP(PAIRF3_STEP)\n','        OVL_LOOP(PAIRF3_STEP)\n        "add x13, x13, #4\\n\\t"  // skip this row\'s private padding before wrap\n')
c=c[:a]+part+c[b:]
old='''        float* d = G->kf + a * G->steps * 4;
        for (long X = 0; X < G->steps; X++, d += 4) {
            d[0] = X < KW ? k[a * KW + X] : 0.f;
            d[1] = X < KW ? k[a1 * KW + X] : 0.f;
            d[2] = X < KW ? k[a2 * KW + X] : 0.f;
            d[3] = (G->kind == 35 && X < KW) ? k[a3 * KW + X] : 0.f;
        }
'''
new='''        if (G->kind == 34) {
            float* d = G->kf + a * (G->steps * 3 + 1);
            for (long X = 0; X < G->steps; X++, d += 3) {
                d[0] = X < KW ? k[a * KW + X] : 0.f;
                d[1] = X < KW ? k[a1 * KW + X] : 0.f;
                d[2] = X < KW ? k[a2 * KW + X] : 0.f;
            }
            // Final LD1RQW stays inside this uniquely owned row chunk.
            d[0] = 0.f;
        } else {
            float* d = G->kf + a * G->steps * 4;
            for (long X = 0; X < G->steps; X++, d += 4) {
                d[0] = X < KW ? k[a * KW + X] : 0.f;
                d[1] = X < KW ? k[a1 * KW + X] : 0.f;
                d[2] = X < KW ? k[a2 * KW + X] : 0.f;
                d[3] = X < KW ? k[a3 * KW + X] : 0.f;
            }
        }
'''
c=once(c,old,new)
c=once(c,'size_t kfneed = (size_t)KH * G->steps * 4 * sizeof(float);','size_t kfneed = (size_t)KH * (G->kind == 34 ? G->steps * 3 + 1 : G->steps * 4) * sizeof(float);')
c=once(c,'            K.kb0 = g->kf + a0 * g->steps * 4; K.kbase = g->kf; K.kend = g->kf + KH * g->steps * 4;',
'''            const long kfrow = g->kind == 34 ? g->steps * 3 + 1 : g->steps * 4;
            K.kb0 = g->kf + a0 * kfrow; K.kbase = g->kf; K.kend = g->kf + KH * kfrow;''')
c=c.replace('// 打包总元素数（R 16/步 + kf 4/步）','// Conservative packing-policy estimate; keep original mode selection')
c=c.replace('kf = pairf3 的三链 b 打包 [KH][steps][4]','kf: F3 [KH][3*steps+1], F4 [KH][4*steps]')
# No group/phase/claim-policy change. Table publication still follows packing.
for marker,end in [('static int roll_groups_base(', 'static inline long roll_phase_sub(')]:
 assert s[s.index(marker):s.index(end)]==c[c.index(marker):c.index(end)]
(root/'baseline.c').write_text(s);(root/'compact.c').write_text(c)
(root/'bench_conv.c').write_bytes(subprocess.check_output(['git','show','138dcac:bench_conv.c']))
files=[root/(n+'.c') for n in ['baseline','compact','bench_conv']]
(out/'sources.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files))
checks=0
for kh in [16,39,55,87,119,247,256]:
 for kw in range(3,401):
  stride=3*kw+1
  for y in range(kh):
   for x in [0,kw//2,kw-1]:
    start=y*stride+3*x
    assert start>=y*stride and start+3<(y+1)*stride
    if x==kw-1:assert start+3==(y+1)*stride-1
    checks+=1
   assert (y*stride+kw*3+1)%(kh*stride)==((y+1)%kh)*stride
print(f'{checks} row-owned load-window cases PASS; all row-end cursors wrap exactly. Complete coefficient contents still require the C packer/guard test.')
print('KH55 KW55 logical F3 table: 48400 -> 36520 bytes (-24.55%); no physical-allocation/RSS or speed claim.')
print((out/'sources.sha256').read_text(),end='')
