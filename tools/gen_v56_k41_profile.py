#!/usr/bin/env python3
"""Separate live first-copy cost, host packing and worker kernels for K41."""
from pathlib import Path
import hashlib,subprocess
from gen_v54 import phase_profile
root=Path('build/v56/experiments/k41-profile');root.mkdir(parents=True,exist_ok=True)
def instrument(source):
    s=phase_profile(source)
    a=s.index('    fprintf(stderr, "[v54-phase]');b=s.index('    if (g_roll_diag)',a)
    part=s[a:b].replace('[v54-phase]','[v56-phase]').replace('pksum/(100.0*nth)','pksum*(1e6/(double)cyc_hz())/nth').replace('/100.0','*(1e6/(double)cyc_hz())')
    s=s[:a]+part+s[b:]
    a=s.index('static void roll_copy_row(')
    s=s[:a]+'static __thread uint64_t first_ticks, first_calls, first_bytes;\nstatic uint64_t first_stats[1024][3];\n'+s[a:]
    a=s.index('static void roll_copy_row(');b=s.index('\n}\n',a)
    f=s[a:b];f=f.replace('{\n    asm volatile(', '{\n    uint64_t first_t0 = cyc();\n    asm volatile(',1)
    f+='\n    first_ticks += cyc() - first_t0; first_calls++; first_bytes += (uint64_t)n * sizeof(float);'
    s=s[:a]+f+s[b:]
    old='    roll_pack_all(P, c->k, KH, KW);'
    s=s.replace(old,'    first_ticks = first_calls = first_bytes = 0;\n'+old,1)
    old='    if (g_roll_diag) D->tot = cyc() - t_start;'
    s=s.replace(old,old+'\n    first_stats[tid][0]=first_ticks; first_stats[tid][1]=first_calls; first_stats[tid][2]=first_bytes;',1)
    a=s.index('static void roll_diag_print(int nth)');b=s.index('{',a)+1
    s=s[:b]+'\n    uint64_t copy_sum=0, calls=0, bytes=0, worker_sum=0;\n    for (int t=0;t<nth;t++) { copy_sum+=first_stats[t][0]; calls+=first_stats[t][1]; bytes+=first_stats[t][2]; worker_sum+=g_rdiag[t].tot; }\n    fprintf(stderr,"[first-copy-cost] mean_worker_us=%.3f mean_copy_us=%.3f copy_pct=%.4f total_calls=%lu total_bytes=%lu\\n",\n            (double)worker_sum/nth*1e6/cyc_hz(),(double)copy_sum/nth*1e6/cyc_hz(),\n            worker_sum?100.0*copy_sum/worker_sum:0,(unsigned long)calls,(unsigned long)bytes);\n'+s[b:]
    # Existing normalized cycles are not actual CPU cycles; scale milliseconds from actual timer.
    s=s.replace('g_rdiag[t].tot / 1e5','g_rdiag[t].tot * (1e3 / (double)cyc_hz())')
    s=s.replace('const double tick_cyc = 1.55e9 / 1e8;', 'const double tick_cyc = 1.55e9 / (double)cyc_hz();')
    return s
for name,rev in [('previous','72b10c2'),('baseline','93163b4')]:
    source=subprocess.check_output(['git','show',rev+':conv2d.c'],text=True)
    for suffix,s in [('',source),('_phase',instrument(source))]:
        p=root/(name+suffix+'.c');p.write_text(s)
        print(hashlib.sha256(s.encode()).hexdigest(),p)
