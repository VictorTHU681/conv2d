// ZA 回写方式对比：mova+st4w vs 直接 ZA 切片存储 + 重载 + st4w vs 仅 mova
// gcc -O2 -march=armv9-a+sme+sve2 zastore.c -o zastore
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + ts.tv_nsec * 1e-9; }
#define VCLOB "z0","z1","z2","z3","z4","z5","z6","z7","z8","z9","z10","z11","z12","z13","z14","z15","p0"

// (a) 一个 tile：4 行 × (4 mova + st4w)
#define MOVA_ROW(T, jc, d)                                                                 \
    "add w12, %w[j" #jc "], #12\n\t add w13, %w[j" #jc "], #8\n\t add w14, %w[j" #jc "], #4\n\t mov w15, %w[j" #jc "]\n\t" \
    "mova z0.s, p0/m, za" #T "v.s[w12, 0]\n\t mova z1.s, p0/m, za" #T "v.s[w13, 0]\n\t"     \
    "mova z2.s, p0/m, za" #T "v.s[w14, 0]\n\t mova z3.s, p0/m, za" #T "v.s[w15, 0]\n\t"     \
    "st4w {z0.s-z3.s}, p0, [%[" #d "]]\n\t"
#define TILE_A(T) MOVA_ROW(T, 0, d0) MOVA_ROW(T, 1, d1) MOVA_ROW(T, 2, d2) MOVA_ROW(T, 3, d3)

// (b) 一个 tile：16 条 ZA 竖切片直接存到 tmp，再 4×(4 ld1w + st4w)
#define ZAST4(T, w, base)                                                                  \
    "st1w {za" #T "v.s[" #w ", 0]}, p0, [x16]\n\t add x16, x16, #64\n\t"                     \
    "st1w {za" #T "v.s[" #w ", 1]}, p0, [x16]\n\t add x16, x16, #64\n\t"                     \
    "st1w {za" #T "v.s[" #w ", 2]}, p0, [x16]\n\t add x16, x16, #64\n\t"                     \
    "st1w {za" #T "v.s[" #w ", 3]}, p0, [x16]\n\t add x16, x16, #64\n\t"
#define RELOAD_ROW(jc, d)                                                                  \
    "add x16, %[t], #" #jc "*64+512\n\t"                                                      \
    "ld1w {z0.s}, p0/z, [x16, #4, mul vl]\n\t ld1w {z1.s}, p0/z, [x16]\n\t"                   \
    "ld1w {z2.s}, p0/z, [x16, #-4, mul vl]\n\t ld1w {z3.s}, p0/z, [x16, #-8, mul vl]\n\t"     \
    "st4w {z0.s-z3.s}, p0, [%[" #d "]]\n\t"
#define TILE_B(T) "mov w12, #0\n\t mov w13, #4\n\t mov w14, #8\n\t mov w15, #12\n\t mov x16, %[t]\n\t" \
    ZAST4(T, w12, 0) ZAST4(T, w13, 1) ZAST4(T, w14, 2) ZAST4(T, w15, 3) \
    RELOAD_ROW(0, d0) RELOAD_ROW(1, d1) RELOAD_ROW(2, d2) RELOAD_ROW(3, d3)

int main(int argc, char** argv)
{
    long iters = argc > 1 ? atol(argv[1]) : 200000;
    float* out = aligned_alloc(256, 1 << 16);
    float* tmp = aligned_alloc(256, 4096);
    memset(out, 0, 1 << 16); memset(tmp, 0, 4096);
    float *d0 = out, *d1 = out + 4096, *d2 = out + 8192, *d3 = out + 12288;   // 4 行输出（相距 16 KB，L1 驻留）
    long j0 = 0, j1 = 1, j2 = 2, j3 = 3;
    for (int mode = 0; mode < 2; mode++) {
        volatile double cyc = 0;
        asm volatile("smstart\n\t" ::: "memory", VCLOB);
        asm volatile("zero {za}\n\t" ::: "memory");
        for (int w = 0; w < 2; w++) {
            long n = w ? iters : iters / 10;
            double t0 = now();
            for (long i = 0; i < n; i++) {
                if (mode == 0)
                    asm volatile("ptrue p0.s\n\t" TILE_A(0) TILE_A(1) TILE_A(2) TILE_A(3)
                                 : : [d0] "r"(d0), [d1] "r"(d1), [d2] "r"(d2), [d3] "r"(d3), [j0] "r"(j0), [j1] "r"(j1), [j2] "r"(j2), [j3] "r"(j3)
                                 : "memory", "x12", "x13", "x14", "x15", VCLOB);
                else
                    asm volatile("ptrue p0.s\n\t" TILE_B(0) TILE_B(1) TILE_B(2) TILE_B(3)
                                 : : [d0] "r"(d0), [d1] "r"(d1), [d2] "r"(d2), [d3] "r"(d3), [t] "r"(tmp)
                                 : "memory", "x12", "x13", "x14", "x15", "x16", VCLOB);
            }
            double t = now() - t0;
            if (w) cyc = t / n * 1.55e9;
        }
        asm volatile("smstop\n\t" ::: "memory", VCLOB);
        printf("  %s: %.1f 周期/pass（4 tile 回写）\n", mode == 0 ? "mova+st4w        " : "ZA st1w+ld1w+st4w", cyc);
    }
    return 0;
}
