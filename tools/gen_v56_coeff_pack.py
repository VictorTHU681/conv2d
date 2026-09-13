#!/usr/bin/env python3
"""Folded coefficient sharing and SVE packing controls over validated v56."""
from pathlib import Path
import subprocess,hashlib
source=subprocess.check_output(['git','show','72b10c2:conv2d.c'],text=True)
root=Path('build/v56/experiments/coefficient-packing');root.mkdir(parents=True,exist_ok=True)
def share(s):
    old='''                size_t kfneed = (size_t)KH * G->steps * 4 * sizeof(float);
                if (g_rbuf[g].kfcap < kfneed) { free(g_rbuf[g].kf); g_rbuf[g].kf = alloc_aligned(kfneed); g_rbuf[g].kfcap = g_rbuf[g].kf ? kfneed : 0; }
                G->kf = g_rbuf[g].kf; G->kfcap = g_rbuf[g].kfcap;'''
    new='''                // Same kind and step count produce identical folded tables.
                // Aliases live only in this call's plan; persistent slots own allocations.
                for (int p = 0; p < g; p++) {
                    const rgrp_t* A = &P->G[p];
                    if (A->kind == G->kind && A->steps == G->steps) {
                        G->kf = A->kf; G->kfcap = A->kfcap;
                        break;
                    }
                }
                if (!G->kf) {
                    size_t kfneed = (size_t)KH * G->steps * 4 * sizeof(float);
                    if (g_rbuf[g].kfcap < kfneed) { free(g_rbuf[g].kf); g_rbuf[g].kf = alloc_aligned(kfneed); g_rbuf[g].kfcap = g_rbuf[g].kf ? kfneed : 0; }
                    G->kf = g_rbuf[g].kf; G->kfcap = g_rbuf[g].kfcap;
                }'''
    assert s.count(old)==1;s=s.replace(old,new)
    old='''        const long a = y;
        const long a1 ='''
    new='''        // The first group using this allocation rebuilds it on every call.
        for (int p = 0; p < i / (int)KH; p++)
            if (P->G[p].kf == G->kf) return;
        const long a = y;
        const long a1 ='''
    assert s.count(old)==1
    return s.replace(old,new)
def vec(s):
    old='''        float* d = G->kf + a * G->steps * 4;
        for (long X = 0; X < G->steps; X++, d += 4) {
            d[0] = X < KW ? k[a * KW + X] : 0.f;
            d[1] = X < KW ? k[a1 * KW + X] : 0.f;
            d[2] = X < KW ? k[a2 * KW + X] : 0.f;
            d[3] = (G->kind == 35 && X < KW) ? k[a3 * KW + X] : 0.f;
        }'''
    new='''        float* d = G->kf + a * G->steps * 4;
        for (long X = 0; X < G->steps; X += (long)svcntw()) {
            svbool_t outp = svwhilelt_b32(X, G->steps);
            svbool_t inp = svwhilelt_b32(X, KW);
            svfloat32_t b0 = svld1_f32(inp, k + a * KW + X);
            svfloat32_t b1 = svld1_f32(inp, k + a1 * KW + X);
            svfloat32_t b2 = svld1_f32(inp, k + a2 * KW + X);
            svfloat32_t b3 = G->kind == 35 ? svld1_f32(inp, k + a3 * KW + X) : svdup_n_f32(0.f);
            svst4_f32(outp, d + X * 4, svcreate4_f32(b0, b1, b2, b3));
        }'''
    assert s.count(old)==1
    return s.replace(old,new)
for name,s in [('baseline',source),('sharekf',share(source)),('veckf',vec(source)),('sharevec',vec(share(source)))]:
    p=root/(name+'.c');p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(),p)
