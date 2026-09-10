// 流式模式 vs 普通模式下 L1 有效容量：工作集 S 内反复 ld1w（对齐 / +4B 非对齐），每条载入的周期数
// gcc -O2 -march=armv9-a+sme+sve2 l1sm.c -o l1sm
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + ts.tv_nsec * 1e-9; }
#define VCLOB "z0","z1","z2","z3","z4","z5","z6","z7","z8","z9","z10","z11","z12","z13","z14","z15","p0"

// 每次迭代 8 条载入，地址 p, p+64, ..., p+448（步幅 512 B），p 在工作集内循环
static double run(const char* buf, long size, long off, long iters)
{
    long steps = size / 512 - 1;          // 每趟 steps 次（每次 8 条载入，覆盖 512 B）
    long passes = iters / steps + 1;
    double t0 = now();
    for (long ps = 0; ps < passes; ps++) {
        const char* p = buf + off;
        long n = steps;
        asm volatile("ptrue p0.s\n\t"
                     "1:\n\t"
                     "ld1w {z0.s}, p0/z, [%[p]]\n\t"
                     "ld1w {z1.s}, p0/z, [%[p], #1, mul vl]\n\t"
                     "ld1w {z2.s}, p0/z, [%[p], #2, mul vl]\n\t"
                     "ld1w {z3.s}, p0/z, [%[p], #3, mul vl]\n\t"
                     "ld1w {z4.s}, p0/z, [%[p], #4, mul vl]\n\t"
                     "ld1w {z5.s}, p0/z, [%[p], #5, mul vl]\n\t"
                     "ld1w {z6.s}, p0/z, [%[p], #6, mul vl]\n\t"
                     "ld1w {z7.s}, p0/z, [%[p], #7, mul vl]\n\t"
                     "add %[p], %[p], #512\n\t"
                     "subs %[n], %[n], #1\n\t"
                     "b.ne 1b\n\t"
                     : [p] "+r"(p), [n] "+r"(n) : : "memory", "cc", VCLOB);
    }
    return (now() - t0) * 1.55e9 / (passes * steps * 8.0);
}

int main(int argc, char** argv)
{
    long iters = argc > 1 ? atol(argv[1]) : 2000000;
    setvbuf(stdout, NULL, _IONBF, 0);
    char* buf = aligned_alloc(4096, 1 << 20);
    memset(buf, 1, 1 << 20);
    long sizes[] = {4, 6, 8, 10, 12, 16, 20, 24, 28, 32, 40, 48, 64, 128, 256};
    for (int sm = 0; sm < 2; sm++) {
        if (sm) asm volatile("smstart\n\t" ::: "memory", VCLOB);
        printf("=== %s\n", sm ? "流式模式 (smstart)" : "普通模式");
        for (int i = 0; i < 15; i++) {
            long S = sizes[i] * 1024;
            double c0 = run(buf, S, 0, iters), c1 = run(buf, S, 4, iters);
            printf("  工作集 %4ld KB: 对齐 %.2f 周期/载入   +4B %.2f 周期/载入\n", sizes[i], c0, c1);
        }
        if (sm) asm volatile("smstop\n\t" ::: "memory", VCLOB);
    }
    return 0;
}
