// 边界行 fmla 方案的干扰探针：真实 1×4+ext 步（5 对齐载入 + 1 b + 4 ext + 4 fmopa）之间每 N 步插入一个
// "fmla 步"（2 tile × 4 ic = 8 条索引 fmla + 1 ld1rqw + a 供数），看 fmopa 步被拖慢多少。
// a 供数两种：U = 2 条非对齐载入；E = 3 条对齐载入 + 2 ext。
// gcc -O2 -march=armv9-a+sme+sve2 brmix.c -o brmix
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + ts.tv_nsec * 1e-9; }
#define VCLOB "z0","z1","z2","z3","z4","z5","z6","z7","z8","z9","z10","z11","z12","z13","z14","z15","z16","z17","z18","z19","z20","z21","z22","z23","z24","z25","z26","z27","z28","z29","z30","z31","p0","p1"
#define OPA(t, a, b) "fmopa za" #t ".s, p0/m, p0/m, z" #a ".s, z" #b ".s\n\t"

// 基本步（与 conv2d.c 的 STEP4X 一致）
#define BSTEP(xa, xb, V0, V1, V2, V3, V4, A0, A1, A2, A3, B) \
    "ld1w {z" #B ".s}, p0/z, [%[" #xb "]]\n\t" \
    "ld1w {z" #V0 ".s}, p0/z, [%[" #xa "]]\n\t" "ld1w {z" #V1 ".s}, p0/z, [%[" #xa "], #1, mul vl]\n\t" \
    "ld1w {z" #V2 ".s}, p0/z, [%[" #xa "], #2, mul vl]\n\t" "ld1w {z" #V3 ".s}, p0/z, [%[" #xa "], #3, mul vl]\n\t" \
    "ld1w {z" #V4 ".s}, p0/z, [%[" #xa "], #4, mul vl]\n\t" \
    "ext z" #A0 ".b, {z" #V0 ".b, z" #V1 ".b}, #12\n\t" "ext z" #A1 ".b, {z" #V1 ".b, z" #V2 ".b}, #12\n\t" \
    "ext z" #A2 ".b, {z" #V2 ".b, z" #V3 ".b}, #12\n\t" "ext z" #A3 ".b, {z" #V3 ".b, z" #V4 ".b}, #12\n\t" \
    OPA(0, A0, B) OPA(1, A1, B) OPA(2, A2, B) OPA(3, A3, B)
#define S1(xa, xb) BSTEP(xa, xb, 8, 9, 10, 11, 12, 0, 1, 2, 3, 4)
#define S2(xa, xb) BSTEP(xa, xb, 16, 17, 18, 19, 20, 21, 22, 23, 13, 14)

// fmla 步 U：2 条非对齐 a（xc 起 +4B）+ 1 ld1rqw + 8 条索引 fmla（累加器 z24..z31）
#define FU(xc, xk) \
    "ld1w {z5.s}, p0/z, [%[" #xc "]]\n\t ld1w {z6.s}, p0/z, [%[" #xc "], #1, mul vl]\n\t" \
    "ld1rqw {z7.s}, p0/z, [%[" #xk "]]\n\t" \
    "fmla z24.s, z5.s, z7.s[0]\n\t fmla z25.s, z5.s, z7.s[1]\n\t fmla z26.s, z5.s, z7.s[2]\n\t fmla z27.s, z5.s, z7.s[3]\n\t" \
    "fmla z28.s, z6.s, z7.s[0]\n\t fmla z29.s, z6.s, z7.s[1]\n\t fmla z30.s, z6.s, z7.s[2]\n\t fmla z31.s, z6.s, z7.s[3]\n\t"
// fmla 步 E：3 条对齐 a + 2 ext + 1 ld1rqw + 8 fmla
// （索引 fmla 的向量-标量操作数必须在 z0..z7：k 放 z3——放在 S2 之后时 z3（S1 的 A3）已死）
#define FE(xc, xk) \
    "ld1w {z5.s}, p0/z, [%[" #xc "]]\n\t ld1w {z6.s}, p0/z, [%[" #xc "], #1, mul vl]\n\t ld1w {z7.s}, p0/z, [%[" #xc "], #2, mul vl]\n\t" \
    "ld1rqw {z3.s}, p0/z, [%[" #xk "]]\n\t" \
    "ext z13.b, {z5.b, z6.b}, #12\n\t ext z15.b, {z6.b, z7.b}, #12\n\t" \
    "fmla z24.s, z13.s, z3.s[0]\n\t fmla z25.s, z13.s, z3.s[1]\n\t fmla z26.s, z13.s, z3.s[2]\n\t fmla z27.s, z13.s, z3.s[3]\n\t" \
    "fmla z28.s, z15.s, z3.s[0]\n\t fmla z29.s, z15.s, z3.s[1]\n\t fmla z30.s, z15.s, z3.s[2]\n\t fmla z31.s, z15.s, z3.s[3]\n\t"
// fmla 步 H：只有一半（1 tile：1 非对齐 a + 4 fmla）
#define FH(xc, xk) \
    "ld1w {z5.s}, p0/z, [%[" #xc "]]\n\t ld1rqw {z7.s}, p0/z, [%[" #xk "]]\n\t" \
    "fmla z24.s, z5.s, z7.s[0]\n\t fmla z25.s, z5.s, z7.s[1]\n\t fmla z26.s, z5.s, z7.s[2]\n\t fmla z27.s, z5.s, z7.s[3]\n\t"

#define OPS : [xa0] "r"(xa0), [xa1] "r"(xa1), [xb0] "r"(xb0), [xb1] "r"(xb1), [xc] "r"(xc), [xk] "r"(xk) : "memory", "cc", VCLOB
#define LOOP(body) asm volatile("ptrue p0.s\n\t 1:\n\t" body "subs %0, %0, #1\n\t b.ne 1b\n\t" : "+r"(n) OPS)

static double run(int mode, long iters, const float* a, const float* b, const float* c)
{
    const float* xa0 = a; const float* xa1 = a + 128;
    const float* xb0 = b + 4; const float* xb1 = b + 68;     // b 16B 对齐（同真实）
    const float* xc = c + 1;                                 // 非对齐 +4B
    const float* xk = b + 256;
    long n = iters;
    asm volatile("smstart\n\t zero {za}\n\t" ::: "memory", VCLOB);   // 流式模式只在计时段内（printf 在流式模式下会 SIGILL）
    double t0 = now();
    switch (mode) {
    case 0: LOOP(S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1)); break;                 // 6 步基线
    case 1: LOOP(S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) FU(xc, xk)); break;      // 6:1 U
    case 2: LOOP(S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) FE(xc, xk)); break;      // 6:1 E
    case 3: LOOP(S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) FU(xc, xk)); break;                                // 4:1 U
    case 4: LOOP(S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) FE(xc, xk)); break;                                // 4:1 E
    case 5: LOOP(S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) FU(xc, xk)); break; // 8:1 U
    case 6: LOOP(S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) FE(xc, xk)); break; // 8:1 E
    case 7: LOOP(S1(xa0, xb0) FU(xc, xk) S2(xa1, xb1) FU(xc, xk) S1(xa0, xb0) FU(xc, xk) S2(xa1, xb1) FU(xc, xk)); break; // 1:1 U（每步 8 fmla）
    case 8: LOOP(S1(xa0, xb0) FH(xc, xk) S2(xa1, xb1) FH(xc, xk) S1(xa0, xb0) FH(xc, xk) S2(xa1, xb1) FH(xc, xk)); break; // 每步 4 fmla（半步 H）
    case 9: LOOP(S1(xa0, xb0) S2(xa1, xb1) FH(xc, xk) S1(xa0, xb0) S2(xa1, xb1) FH(xc, xk)); break;                     // 2:1 H（每步 2 fmla）
    case 10: LOOP(S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) FH(xc, xk) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) FH(xc, xk)); break; // 3:1 H
    case 11: LOOP(FU(xc, xk) FU(xc, xk) FU(xc, xk) FU(xc, xk)); break;                                                  // 仅 fmla 步 U ×4
    case 12: LOOP(FE(xc, xk) FE(xc, xk) FE(xc, xk) FE(xc, xk)); break;                                                  // 仅 fmla 步 E ×4
    case 13: LOOP(S1(xa0, xb0) S1(xa1, xb1) S1(xa0, xb0) S1(xa1, xb1) S1(xa0, xb0) S1(xa1, xb1)); break;                 // 单寄存器组基线
    case 14: LOOP(S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) FU(xc, xk) S2(xa1, xb1) S1(xa0, xb0) S2(xa1, xb1) FU(xc, xk)); break; // 3:1 U (2.67/步)
    case 15: LOOP(S1(xa0, xb0) S2(xa1, xb1) S1(xa0, xb0) FU(xc, xk) S2(xa1, xb1) S1(xa0, xb0) FU(xc, xk)); break;       // 5:2 U (3.2/步)
    case 16: LOOP(S1(xa0, xb0) S1(xa1, xb1) S1(xa0, xb0) S1(xa1, xb1) FU(xc, xk)); break;                                // 单组 4:1 U
    case 17: LOOP(S1(xa0, xb0) S1(xa1, xb1) S1(xa0, xb0) FU(xc, xk) S1(xa1, xb1) S1(xa0, xb0) S1(xa1, xb1) FU(xc, xk)); break; // 单组 3:1 U
    }
    double t = now() - t0;
    asm volatile("smstop\n\t" ::: "memory", VCLOB);
    return t;
}

int main(int argc, char** argv)
{
    double ghz = argc > 1 ? atof(argv[1]) : 1.55;
    setvbuf(stdout, NULL, _IONBF, 0);
    float* a = aligned_alloc(256, 1 << 16); float* b = aligned_alloc(256, 1 << 16); float* c = aligned_alloc(256, 1 << 16);
    memset(a, 0, 1 << 16); memset(b, 0, 1 << 16); memset(c, 0, 1 << 16);
    long iters = 3000000;
    struct { int mode; int nstep; int nfstep; const char* name; } T[] = {
        {0, 6, 0, "6 步基线（1x4+ext）"},
        {5, 8, 1, "8:1 U（每步 +1 fmla, +0.25 ld）"},
        {6, 8, 1, "8:1 E（每步 +1 fmla, +0.25 ext）"},
        {1, 6, 1, "6:1 U（每步 +1.33 fmla）"},
        {2, 6, 1, "6:1 E（每步 +1.33 fmla, +0.33 ext）"},
        {3, 4, 1, "4:1 U（每步 +2 fmla）"},
        {4, 4, 1, "4:1 E（每步 +2 fmla, +0.5 ext）"},
        {10, 6, 2, "3:1 H（每步 +1.33 fmla）"},
        {9, 4, 2, "2:1 H（每步 +2 fmla）"},
        {8, 4, 4, "1:1 H（每步 +4 fmla）"},
        {7, 4, 4, "1:1 U（每步 +8 fmla）"},
        {11, 0, 4, "仅 fmla 步 U ×4"},
        {12, 0, 4, "仅 fmla 步 E ×4"},
        {13, 6, 0, "6 步基线 单寄存器组"},
        {14, 6, 2, "3:1 U（每步 +2.67 fmla）"},
        {15, 5, 2, "5:2 U（每步 +3.2 fmla）"},
        {16, 4, 1, "单组 4:1 U（每步 +2 fmla）"},
        {17, 6, 2, "单组 3:1 U（每步 +2.67 fmla）"},
    };
    int nT = sizeof(T) / sizeof(T[0]);
    for (int m = 0; m < nT; m++) {
        run(T[m].mode, iters / 10, a, b, c);
        double t = run(T[m].mode, iters, a, b, c);
        double cyc = t * ghz * 1e9 / iters;
        if (T[m].nstep)
            printf("  [%2d] %-42s %7.2f 周期/迭代  %6.2f 周期/fmopa步 (%+.1f%%)\n", m, T[m].name, cyc, cyc / T[m].nstep, (cyc / T[m].nstep / 8.0 - 1) * 100);
        else
            printf("  [%2d] %-42s %7.2f 周期/迭代  %6.2f 周期/fmla步\n", m, T[m].name, cyc, cyc / T[m].nfstep);
    }
    return 0;
}
