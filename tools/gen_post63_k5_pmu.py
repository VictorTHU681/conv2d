#!/usr/bin/env python3
"""Shared-image K5 controls and per-worker user PMU diagnostics outside SME mode."""
from pathlib import Path
import hashlib,subprocess,re

root=Path('build/post63/k5-pmu');out=Path('results/post63/k5-pmu')
root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
parent=Path('build/post63/k5-copy-order')
digests={'baseline':'0136da05ea4658fb5792412e95baaec0e38ff299b176e5de681f228bca88da93',
         'early':'2646115f81bafc08b178a22306bfb5c112808f62f7469e0a8bd60f90998b4a3b',
         'spread':'be35f717d52620fb862f203c8b2c98d4ab5aa0f37373ae68c8c3670850c83eba'}
versions={}
for v,h in digests.items():
    data=(parent/(v+'.c')).read_text();assert hashlib.sha256(data.encode()).hexdigest()==h
    versions[v]=data
source=versions['baseline'];signature='static __attribute__((noinline)) void k5('
a=source.index(signature);b=source.index('\n}\n',a)+3
functions=[]
for v,s in versions.items():
    i=s.index(signature);j=s.index('\n}\n',i)+3
    body=s[i:j]
    name='k5' if v=='baseline' else 'k5_'+v
    body=body.replace(signature,f'static __attribute__((noinline, aligned(128))) void {name}(',1)
    functions.append(body)
s=source[:a]+'\n'.join(functions)+'\nstatic void (*g_diag_k5_fn)(const kp_t*);\n'+source[b:]
old='static void read_knobs(void)';assert s.count(old)==1
s=s.replace(old,'static int g_diag_k5_mode, g_diag_pmu_enabled;\n'+old)
old='    if (g_knobs.inited) return;';assert s.count(old)==1
s=s.replace(old,old+'''
    g_diag_k5_mode=env_int("CONV_K5_ORDER",0);
    g_diag_pmu_enabled=env_int("CONV_K5_PMU",1);
    if((unsigned)g_diag_k5_mode>2 || (unsigned)g_diag_pmu_enabled>1) { fprintf(stderr,"PMU_CONFIG_INVALID\\n");exit(2); }''')
a=s.index('static void roll_worker(')
s=s[:a]+Path('tools/post63_pmu_scope.inc').read_text()+'\n'+s[a:]
a=s.index('static void roll_worker(');b=s.index('\n}\n',a)+3
worker=s[a:b]
assert worker.count('    sme_start();')==worker.count('    sme_stop();')==1
worker=worker.replace('    sme_start();','    diag_pmu_begin();\n    sme_start();')
worker=worker.replace('    sme_stop();','    sme_stop();\n    diag_pmu_end(tid);')
assert worker.count('k5(&K)')==1
worker=worker.replace('k5(&K)','g_diag_k5_fn(&K)')
s=s[:a]+worker+s[b:]
a=s.index('static void conv2d_roll(')
b=s.index('    run_parallel(nth, &ctx, g_knobs.pool);',a)
s=s[:b]+'''    void (*choices[3])(const kp_t*)={k5,k5_early,k5_spread};
    g_diag_k5_fn=choices[g_diag_k5_mode];
    memset(diag_pmu_records,0,(size_t)nth*sizeof(diag_pmu_records[0]));
'''+s[b:]
(root/'candidate.c').write_text(s)
subprocess.run(['python3','tools/gen_v56_k5_profile.py','--root',str(root),'--variants','candidate','--table-counts','--thread-detail'],check=True,stdout=subprocess.DEVNULL)
s=(root/'candidate_profile.c').read_text()
old_pack='    diag_pmu_begin();\n    k5_pack_ticks[tid]=cyc()-k5_pack_begin;'
new_pack='    k5_pack_ticks[tid]=cyc()-k5_pack_begin;\n    diag_pmu_begin();'
assert s.count(old_pack)==1
s=s.replace(old_pack,new_pack)
old='    if (g_roll_diag) roll_diag_print(nth);';assert s.count(old)==1
new='''    for(int t=0;t<nth;t++) {
        const diag_pmu_record_t* d=&diag_pmu_records[t];
        fprintf(stderr,"K5_PMU call=%lu tid=%d enabled=%d user_cycles=%lu user_instructions=%lu enabled_ns=%lu running_ns=%lu scope_us=%.3f\\n",
                call,t,g_diag_pmu_enabled,(unsigned long)d->cycles,(unsigned long)d->instructions,
                (unsigned long)d->enabled_ns,(unsigned long)d->running_ns,(double)d->ticks*1e6/cyc_hz());
    }
'''+old
s=s.replace(old,new)
(root/'pmu.c').write_text(s)
(root/'fbench.c').write_bytes(subprocess.check_output(['git','show','8b6b295:tools/fbench.c']))
assert hashlib.sha256((root/'fbench.c').read_bytes()).hexdigest()=='e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad'
files=[root/(v+'.c') for v in ['candidate','pmu','fbench']]
manifest=''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in files)
(out/'sources.sha256').write_text(manifest)
print(manifest,end='')
print('Diagnostic-only image: aligned K5 alternatives, read-once mode, same indirect call site, per-thread user cycles/instructions around the whole SME worker loop. All perf syscalls are before sme_start or after sme_stop. No syscall is inserted inside active streaming mode; enabled/running time uses per-call differences.')
