#!/usr/bin/env python3
"""Separate actual executed tile steps, packing and host preparation."""
from pathlib import Path
import hashlib

root=Path('build/v56/experiments/k5-triplet')
def once(s,old,new):
    assert s.count(old)==1,(s.count(old),old[:80])
    return s.replace(old,new)
for name in ['baseline','triplet']:
    s=(root/(name+'.c')).read_text()
    s=once(s,'static rdiag_t g_rdiag[1024];',
           'static rdiag_t g_rdiag[1024];\nstatic uint64_t k5_pack_ticks[1024];\nstatic unsigned long k5_profile_call;')
    s=once(s,'    if (tid >= nth || tid >= P->pnth) return;',
           '    if (tid >= nth || tid >= P->pnth) return;\n    uint64_t k5_pack_begin=cyc();')
    a=s.index('static void roll_worker(');b=s.index('    sme_start();',a)
    s=s[:b]+'    k5_pack_ticks[tid]=cyc()-k5_pack_begin;\n'+s[b:]
    s=once(s,'D->ts[ki] += 4L * g->steps * (rows);',
           'D->ts[ki] += 4L * (g->kind == 5 ? KW + 2 : g->kind == 4 ? KW + 3 : g->steps) * rows;')
    s=once(s,'    roll_prepare(k, H, W, KH, KW, nth);',
           '    uint64_t k5_t0=cyc();\n    roll_prepare(k, H, W, KH, KW, nth);\n    uint64_t k5_t1=cyc();')
    old='    run_parallel(nth, &ctx, g_knobs.pool);\n    if (g_roll_diag)'
    new='''    uint64_t k5_t2=cyc();
    run_parallel(nth, &ctx, g_knobs.pool);
    uint64_t k5_t3=cyc(),pk=0,pkmax=0; double hz=(double)cyc_hz();
    unsigned long call=++k5_profile_call;
    for(int t=0;t<nth;t++) { pk+=k5_pack_ticks[t]; if(k5_pack_ticks[t]>pkmax)pkmax=k5_pack_ticks[t]; }
    fprintf(stderr,"K5_PHASE call=%lu prepare_us=%.3f dispatch_us=%.3f workers_us=%.3f pack_mean_us=%.3f pack_max_us=%.3f\\n",
            call,(k5_t1-k5_t0)*1e6/hz,(k5_t2-k5_t1)*1e6/hz,(k5_t3-k5_t2)*1e6/hz,pk*1e6/hz/nth,pkmax*1e6/hz);
    for(int bucket=0;bucket<4;bucket++) {
        uint64_t tk=0; long ts=0;
        for(int t=0;t<nth;t++) { tk+=g_rdiag[t].tk[bucket]; ts+=g_rdiag[t].ts[bucket]; }
        if(ts) fprintf(stderr,"K5_COST call=%lu bucket=%d tile_steps=%ld kernel_mean_us=%.3f ns_per_tile_step=%.6f\\n",
                       call,bucket,ts,tk*1e6/hz/nth,tk*1e9/hz/ts);
    }
    if (g_roll_diag)'''
    s=once(s,old,new)
    s=s.replace('1.55e9 / 1e8','1.55e9 / (double)cyc_hz()').replace('g_rdiag[t].tot / 1e5','g_rdiag[t].tot * (1e3/(double)cyc_hz())')
    p=root/(name+'_profile.c');p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),p)
