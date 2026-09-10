// FP32 SME 微基准：fmopa.s 吞吐/延迟、配合 ld1w（对齐/非对齐）与 ld4w 的供数、流式 SVE fmla.s
// gcc -O2 -march=armv9-a+sme+sve2 smef32.c -o smef32
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + ts.tv_nsec * 1e-9; }
#define VCLOB "z0","z1","z2","z3","z4","z5","z6","z7","z8","z9","z10","z11","z12","z13","z14","z15","z16","z17","z18","z19","z20","z21","z22","z23","z24","z25","z26","z27","z28","z29","z30","z31","p0","p1"

#define OPA(t, a, b) "fmopa za" #t ".s, p0/m, p0/m, z" #a ".s, z" #b ".s\n\t"
#define LDA(r, base, off) "ld1w {z" #r ".s}, p0/z, [%[" #base "], #" #off ", mul vl]\n\t"
#define LDB(r, base) "ld1w {z" #r ".s}, p0/z, [%[" #base "]]\n\t"
// 一步：b 载入 + 4 个 a 载入 + 4 fmopa（a 寄存器 a0..a0+3，b 寄存器 bb）
#define STEP(a0, a1, a2, a3, bb, xa, xb) \
    LDB(bb, xb) LDA(a0, xa, 0) LDA(a1, xa, 1) LDA(a2, xa, 2) LDA(a3, xa, 3) \
    OPA(0, a0, bb) OPA(1, a1, bb) OPA(2, a2, bb) OPA(3, a3, bb)
#define STEP_NOLD(a0, a1, a2, a3, bb) OPA(0, a0, bb) OPA(1, a1, bb) OPA(2, a2, bb) OPA(3, a3, bb)
#define STEP_LDONLY(a0, a1, a2, a3, bb, xa, xb) \
    LDB(bb, xb) LDA(a0, xa, 0) LDA(a1, xa, 1) LDA(a2, xa, 2) LDA(a3, xa, 3)

static double run(int mode, long iters, const float* a, const float* b, long aoff, long boff)
{
    const float* xa0 = a + aoff;
    const float* xa1 = a + aoff + 128;
    const float* xa2 = a + aoff + 256;
    const float* xa3 = a + aoff + 384;
    const float* xb0 = b + boff;
    const float* xb1 = b + boff + 64;
    const float* xb2 = b + boff + 128;
    const float* xb3 = b + boff + 192;
    long n = iters;
    double t0 = now();
    switch (mode) {
    case 0: // 4 fmopa 轮转 4 tile，无载入
        asm volatile("ptrue p0.s\n\t 1:\n\t" STEP_NOLD(0, 1, 2, 3, 4) "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : : "memory", "cc", VCLOB);
        break;
    case 1: // 同一 tile 连续 4 条 → 延迟
        asm volatile("ptrue p0.s\n\t 1:\n\t" OPA(0, 0, 4) OPA(0, 1, 4) OPA(0, 2, 4) OPA(0, 3, 4) "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : : "memory", "cc", VCLOB);
        break;
    case 2: // 两 tile 交替
        asm volatile("ptrue p0.s\n\t 1:\n\t" OPA(0, 0, 4) OPA(1, 1, 4) OPA(0, 2, 4) OPA(1, 3, 4) "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : : "memory", "cc", VCLOB);
        break;
    case 3: // 4 步：每步 5 载入 + 4 fmopa（地址固定，由 aoff/boff 决定对齐）
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP(0, 1, 2, 3, 4, xa0, xb0) STEP(8, 9, 10, 11, 12, xa1, xb1)
                     STEP(16, 17, 18, 19, 20, xa2, xb2) STEP(24, 25, 26, 27, 28, xa3, xb3)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    case 4: // 仅载入（同 3 的载入）
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP_LDONLY(0, 1, 2, 3, 4, xa0, xb0) STEP_LDONLY(8, 9, 10, 11, 12, xa1, xb1)
                     STEP_LDONLY(16, 17, 18, 19, 20, xa2, xb2) STEP_LDONLY(24, 25, 26, 27, 28, xa3, xb3)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    case 5: // 4 × ld4w（地址由 aoff 决定对齐）
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     "ld4w {z0.s-z3.s}, p0/z, [%[xa0]]\n\t"
                     "ld4w {z8.s-z11.s}, p0/z, [%[xa1]]\n\t"
                     "ld4w {z16.s-z19.s}, p0/z, [%[xa2]]\n\t"
                     "ld4w {z24.s-z27.s}, p0/z, [%[xa3]]\n\t"
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3) : "memory", "cc", VCLOB);
        break;
    case 6: // 16 fmopa + 4 ld4w + 4 ld1w(b)：ld4w 的 4 个向量分别喂 4 步的同一 tile
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     "ld4w {z0.s-z3.s}, p0/z, [%[xa0]]\n\t" LDB(4, xb0)
                     OPA(0, 0, 4) OPA(1, 1, 4) OPA(2, 2, 4) OPA(3, 3, 4)
                     "ld4w {z8.s-z11.s}, p0/z, [%[xa1]]\n\t" LDB(12, xb1)
                     OPA(0, 8, 12) OPA(1, 9, 12) OPA(2, 10, 12) OPA(3, 11, 12)
                     "ld4w {z16.s-z19.s}, p0/z, [%[xa2]]\n\t" LDB(20, xb2)
                     OPA(0, 16, 20) OPA(1, 17, 20) OPA(2, 18, 20) OPA(3, 19, 20)
                     "ld4w {z24.s-z27.s}, p0/z, [%[xa3]]\n\t" LDB(28, xb3)
                     OPA(0, 24, 28) OPA(1, 25, 28) OPA(2, 26, 28) OPA(3, 27, 28)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    case 7: // 流式模式 SVE fmla.s 吞吐（16 条独立）
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     "fmla z8.s, p0/m, z0.s, z1.s\n\t fmla z9.s, p0/m, z0.s, z1.s\n\t fmla z10.s, p0/m, z0.s, z1.s\n\t fmla z11.s, p0/m, z0.s, z1.s\n\t"
                     "fmla z12.s, p0/m, z0.s, z1.s\n\t fmla z13.s, p0/m, z0.s, z1.s\n\t fmla z14.s, p0/m, z0.s, z1.s\n\t fmla z15.s, p0/m, z0.s, z1.s\n\t"
                     "fmla z16.s, p0/m, z0.s, z1.s\n\t fmla z17.s, p0/m, z0.s, z1.s\n\t fmla z18.s, p0/m, z0.s, z1.s\n\t fmla z19.s, p0/m, z0.s, z1.s\n\t"
                     "fmla z20.s, p0/m, z0.s, z1.s\n\t fmla z21.s, p0/m, z0.s, z1.s\n\t fmla z22.s, p0/m, z0.s, z1.s\n\t fmla z23.s, p0/m, z0.s, z1.s\n\t"
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : : "memory", "cc", VCLOB);
        break;
    case 8: // 16 fmopa + 16 fmla.s 交错（并发发射测试）
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     OPA(0, 0, 4) "fmla z8.s, p0/m, z0.s, z1.s\n\t" OPA(1, 1, 4) "fmla z9.s, p0/m, z0.s, z1.s\n\t"
                     OPA(2, 2, 4) "fmla z10.s, p0/m, z0.s, z1.s\n\t" OPA(3, 3, 4) "fmla z11.s, p0/m, z0.s, z1.s\n\t"
                     OPA(0, 0, 4) "fmla z12.s, p0/m, z0.s, z1.s\n\t" OPA(1, 1, 4) "fmla z13.s, p0/m, z0.s, z1.s\n\t"
                     OPA(2, 2, 4) "fmla z14.s, p0/m, z0.s, z1.s\n\t" OPA(3, 3, 4) "fmla z15.s, p0/m, z0.s, z1.s\n\t"
                     OPA(0, 0, 4) "fmla z16.s, p0/m, z0.s, z1.s\n\t" OPA(1, 1, 4) "fmla z17.s, p0/m, z0.s, z1.s\n\t"
                     OPA(2, 2, 4) "fmla z18.s, p0/m, z0.s, z1.s\n\t" OPA(3, 3, 4) "fmla z19.s, p0/m, z0.s, z1.s\n\t"
                     OPA(0, 0, 4) "fmla z20.s, p0/m, z0.s, z1.s\n\t" OPA(1, 1, 4) "fmla z21.s, p0/m, z0.s, z1.s\n\t"
                     OPA(2, 2, 4) "fmla z22.s, p0/m, z0.s, z1.s\n\t" OPA(3, 3, 4) "fmla z23.s, p0/m, z0.s, z1.s\n\t"
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : : "memory", "cc", VCLOB);
        break;
    case 9: // 16 fmopa + 32 fmla.s（每 fmopa 2 条）
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     OPA(0, 0, 4) "fmla z8.s, p0/m, z0.s, z1.s\n\t fmla z9.s, p0/m, z0.s, z1.s\n\t"
                     OPA(1, 1, 4) "fmla z10.s, p0/m, z0.s, z1.s\n\t fmla z11.s, p0/m, z0.s, z1.s\n\t"
                     OPA(2, 2, 4) "fmla z12.s, p0/m, z0.s, z1.s\n\t fmla z13.s, p0/m, z0.s, z1.s\n\t"
                     OPA(3, 3, 4) "fmla z14.s, p0/m, z0.s, z1.s\n\t fmla z15.s, p0/m, z0.s, z1.s\n\t"
                     OPA(0, 0, 4) "fmla z16.s, p0/m, z0.s, z1.s\n\t fmla z17.s, p0/m, z0.s, z1.s\n\t"
                     OPA(1, 1, 4) "fmla z18.s, p0/m, z0.s, z1.s\n\t fmla z19.s, p0/m, z0.s, z1.s\n\t"
                     OPA(2, 2, 4) "fmla z20.s, p0/m, z0.s, z1.s\n\t fmla z21.s, p0/m, z0.s, z1.s\n\t"
                     OPA(3, 3, 4) "fmla z22.s, p0/m, z0.s, z1.s\n\t fmla z23.s, p0/m, z0.s, z1.s\n\t"
                     OPA(0, 0, 4) "fmla z8.s, p0/m, z0.s, z1.s\n\t fmla z9.s, p0/m, z0.s, z1.s\n\t"
                     OPA(1, 1, 4) "fmla z10.s, p0/m, z0.s, z1.s\n\t fmla z11.s, p0/m, z0.s, z1.s\n\t"
                     OPA(2, 2, 4) "fmla z12.s, p0/m, z0.s, z1.s\n\t fmla z13.s, p0/m, z0.s, z1.s\n\t"
                     OPA(3, 3, 4) "fmla z14.s, p0/m, z0.s, z1.s\n\t fmla z15.s, p0/m, z0.s, z1.s\n\t"
                     OPA(0, 0, 4) "fmla z16.s, p0/m, z0.s, z1.s\n\t fmla z17.s, p0/m, z0.s, z1.s\n\t"
                     OPA(1, 1, 4) "fmla z18.s, p0/m, z0.s, z1.s\n\t fmla z19.s, p0/m, z0.s, z1.s\n\t"
                     OPA(2, 2, 4) "fmla z20.s, p0/m, z0.s, z1.s\n\t fmla z21.s, p0/m, z0.s, z1.s\n\t"
                     OPA(3, 3, 4) "fmla z22.s, p0/m, z0.s, z1.s\n\t fmla z23.s, p0/m, z0.s, z1.s\n\t"
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : : "memory", "cc", VCLOB);
        break;
#define FI4(a, k, r0, r1, r2, r3) \
    "fmla z" #r0 ".s, z" #a ".s, z" #k ".s[0]\n\t fmla z" #r1 ".s, z" #a ".s, z" #k ".s[1]\n\t" \
    "fmla z" #r2 ".s, z" #a ".s, z" #k ".s[2]\n\t fmla z" #r3 ".s, z" #a ".s, z" #k ".s[3]\n\t"
    case 10: // 16 fmopa + 64 fmla.s 索引（每 fmopa 4 条，5 行方案）
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     OPA(0, 0, 4) FI4(0, 5, 8, 9, 10, 11) OPA(1, 1, 4) FI4(1, 5, 12, 13, 14, 15)
                     OPA(2, 2, 4) FI4(2, 5, 16, 17, 18, 19) OPA(3, 3, 4) FI4(3, 5, 20, 21, 22, 23)
                     OPA(0, 0, 4) FI4(0, 5, 8, 9, 10, 11) OPA(1, 1, 4) FI4(1, 5, 12, 13, 14, 15)
                     OPA(2, 2, 4) FI4(2, 5, 16, 17, 18, 19) OPA(3, 3, 4) FI4(3, 5, 20, 21, 22, 23)
                     OPA(0, 0, 4) FI4(0, 5, 8, 9, 10, 11) OPA(1, 1, 4) FI4(1, 5, 12, 13, 14, 15)
                     OPA(2, 2, 4) FI4(2, 5, 16, 17, 18, 19) OPA(3, 3, 4) FI4(3, 5, 20, 21, 22, 23)
                     OPA(0, 0, 4) FI4(0, 5, 8, 9, 10, 11) OPA(1, 1, 4) FI4(1, 5, 12, 13, 14, 15)
                     OPA(2, 2, 4) FI4(2, 5, 16, 17, 18, 19) OPA(3, 3, 4) FI4(3, 5, 20, 21, 22, 23)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : : "memory", "cc", VCLOB);
        break;
    // 真实形态：每步 1 b + 4 a + 1 ld1rqw + 4 fmopa + 16 fmla 索引；a 用 z0-3 / z24-27 双缓冲，b z4/z28，k z5/z6
#define STEPF(xa, xb, A0, A1, A2, A3, B, K) \
    LDB(B, xb) LDA(A0, xa, 0) LDA(A1, xa, 1) LDA(A2, xa, 2) LDA(A3, xa, 3) \
    "ld1rqw {z" #K ".s}, p0/z, [%[" #xb "], #16]\n\t" \
    OPA(0, A0, B) FI4(A0, K, 8, 9, 10, 11) OPA(1, A1, B) FI4(A1, K, 12, 13, 14, 15) \
    OPA(2, A2, B) FI4(A2, K, 16, 17, 18, 19) OPA(3, A3, B) FI4(A3, K, 20, 21, 22, 23)
    case 11:
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEPF(xa0, xb0, 0, 1, 2, 3, 4, 5) STEPF(xa1, xb1, 24, 25, 26, 27, 28, 6)
                     STEPF(xa2, xb2, 0, 1, 2, 3, 4, 5) STEPF(xa3, xb3, 24, 25, 26, 27, 28, 6)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    // 每步 2 条 fmla 索引（8 条/步，两 tile 的第 5 行）
#define FI2(a, k, r0, r1) "fmla z" #r0 ".s, z" #a ".s, z" #k ".s[0]\n\t fmla z" #r1 ".s, z" #a ".s, z" #k ".s[1]\n\t"
#define STEPG(xa, xb, A0, A1, A2, A3, B, K) \
    LDB(B, xb) LDA(A0, xa, 0) LDA(A1, xa, 1) LDA(A2, xa, 2) LDA(A3, xa, 3) \
    "ld1rqw {z" #K ".s}, p0/z, [%[" #xb "], #16]\n\t" \
    OPA(0, A0, B) FI2(A0, K, 8, 9) OPA(1, A1, B) FI2(A1, K, 12, 13) \
    OPA(2, A2, B) FI2(A2, K, 16, 17) OPA(3, A3, B) FI2(A3, K, 20, 21)
    case 12:
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEPG(xa0, xb0, 0, 1, 2, 3, 4, 5) STEPG(xa1, xb1, 24, 25, 26, 27, 28, 6)
                     STEPG(xa2, xb2, 0, 1, 2, 3, 4, 5) STEPG(xa3, xb3, 24, 25, 26, 27, 28, 6)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
#define PF(base, off) "prfm pldl1keep, [%[" #base "], #" #off "]\n\t"
    case 13: // 16 fmopa + 20 ld1w（a 非对齐，b 16B）+ 4×N prfm（N=aoff 传入的次数：这里固定 5/步组 → 20/迭代）
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP(0, 1, 2, 3, 4, xa0, xb0) PF(xa0, 4096) PF(xa1, 4096) PF(xa2, 4096) PF(xa3, 4096) PF(xb0, 4096)
                     STEP(8, 9, 10, 11, 12, xa1, xb1) PF(xa0, 4160) PF(xa1, 4160) PF(xa2, 4160) PF(xa3, 4160) PF(xb0, 4160)
                     STEP(16, 17, 18, 19, 20, xa2, xb2) PF(xa0, 4224) PF(xa1, 4224) PF(xa2, 4224) PF(xa3, 4224) PF(xb0, 4224)
                     STEP(24, 25, 26, 27, 28, xa3, xb3) PF(xa0, 4288) PF(xa1, 4288) PF(xa2, 4288) PF(xa3, 4288) PF(xb0, 4288)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    case 14: // 同 13 但每迭代只 5 条 prfm
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP(0, 1, 2, 3, 4, xa0, xb0) PF(xa0, 4096) PF(xb0, 4096)
                     STEP(8, 9, 10, 11, 12, xa1, xb1) PF(xa1, 4096)
                     STEP(16, 17, 18, 19, 20, xa2, xb2) PF(xa2, 4096)
                     STEP(24, 25, 26, 27, 28, xa3, xb3) PF(xa3, 4096)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    // 2×2 排布：每步 2 a（非对齐）+ 2 b + 4 fmopa
#define STEP22(A0, A1, B0, B1, xa, xb) \
    LDB(B0, xb) "ld1w {z" #B1 ".s}, p0/z, [%[" #xb "], #2, mul vl]\n\t" LDA(A0, xa, 0) LDA(A1, xa, 1) \
    OPA(0, A0, B0) OPA(1, A1, B0) OPA(2, A0, B1) OPA(3, A1, B1)
    case 15:
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP22(0, 1, 4, 5, xa0, xb0) STEP22(8, 9, 12, 13, xa1, xb1)
                     STEP22(16, 17, 20, 21, xa2, xb2) STEP22(24, 25, 28, 29, xa3, xb3)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    case 16: // 2×2 + 每迭代 8 prfm
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP22(0, 1, 4, 5, xa0, xb0) PF(xa0, 4096) PF(xb0, 4096)
                     STEP22(8, 9, 12, 13, xa1, xb1) PF(xa1, 4096) PF(xb1, 4096)
                     STEP22(16, 17, 20, 21, xa2, xb2) PF(xa2, 4096) PF(xb2, 4096)
                     STEP22(24, 25, 28, 29, xa3, xb3) PF(xa3, 4096) PF(xb3, 4096)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    // 4×1 排布：每步 1 a（非对齐）+ 4 b（对齐由 boff 决定）+ 4 fmopa
#define STEP41(A0, B0, B1, B2, B3, xa, xb) \
    LDA(A0, xa, 0) LDB(B0, xb) "ld1w {z" #B1 ".s}, p0/z, [%[" #xb "], #1, mul vl]\n\t" \
    "ld1w {z" #B2 ".s}, p0/z, [%[" #xb "], #2, mul vl]\n\t" "ld1w {z" #B3 ".s}, p0/z, [%[" #xb "], #3, mul vl]\n\t" \
    OPA(0, A0, B0) OPA(1, A0, B1) OPA(2, A0, B2) OPA(3, A0, B3)
    case 17:
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP41(0, 4, 5, 6, 7, xa0, xb0) STEP41(8, 12, 13, 14, 15, xa1, xb1)
                     STEP41(16, 20, 21, 22, 23, xa2, xb2) STEP41(24, 28, 29, 30, 31, xa3, xb3)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    case 18: // 仅 20 ld1w：a 非对齐 +4B，b 对齐（区分 a/b 非对齐的贡献）
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP_LDONLY(0, 1, 2, 3, 4, xa0, xb0) STEP_LDONLY(8, 9, 10, 11, 12, xa1, xb1)
                     STEP_LDONLY(16, 17, 18, 19, 20, xa2, xb2) STEP_LDONLY(24, 25, 26, 27, 28, xa3, xb3)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    // 1×4 + ext：每步 5 条对齐 a 载入（z8-z12 / z16-z20 交替）+ 1 条 b + 4 条 ext（构造式）+ 4 fmopa
#define STEPX(xa, xb, V0, V1, V2, V3, V4, A0, A1, A2, A3, B) \
    "ld1w {z" #V0 ".s}, p0/z, [%[" #xa "]]\n\t" "ld1w {z" #V1 ".s}, p0/z, [%[" #xa "], #1, mul vl]\n\t" \
    "ld1w {z" #V2 ".s}, p0/z, [%[" #xa "], #2, mul vl]\n\t" "ld1w {z" #V3 ".s}, p0/z, [%[" #xa "], #3, mul vl]\n\t" \
    "ld1w {z" #V4 ".s}, p0/z, [%[" #xa "], #4, mul vl]\n\t" LDB(B, xb) \
    "ext z" #A0 ".b, {z" #V0 ".b, z" #V1 ".b}, #12\n\t" "ext z" #A1 ".b, {z" #V1 ".b, z" #V2 ".b}, #12\n\t" \
    "ext z" #A2 ".b, {z" #V2 ".b, z" #V3 ".b}, #12\n\t" "ext z" #A3 ".b, {z" #V3 ".b, z" #V4 ".b}, #12\n\t" \
    OPA(0, A0, B) OPA(1, A1, B) OPA(2, A2, B) OPA(3, A3, B)
    case 19:
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEPX(xa0, xb0, 8, 9, 10, 11, 12, 0, 1, 2, 3, 4) STEPX(xa1, xb1, 16, 17, 18, 19, 20, 24, 25, 26, 27, 28)
                     STEPX(xa2, xb2, 8, 9, 10, 11, 12, 0, 1, 2, 3, 4) STEPX(xa3, xb3, 16, 17, 18, 19, 20, 24, 25, 26, 27, 28)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    // 2×2 + ext：每步 3 条对齐 a 载入 + 2 条 ext + 2 b + 4 fmopa
#define STEPY(xa, xb, V0, V1, V2, A0, A1, B0, B1) \
    "ld1w {z" #V0 ".s}, p0/z, [%[" #xa "]]\n\t" "ld1w {z" #V1 ".s}, p0/z, [%[" #xa "], #1, mul vl]\n\t" \
    "ld1w {z" #V2 ".s}, p0/z, [%[" #xa "], #2, mul vl]\n\t" LDB(B0, xb) "ld1w {z" #B1 ".s}, p0/z, [%[" #xb "], #2, mul vl]\n\t" \
    "ext z" #A0 ".b, {z" #V0 ".b, z" #V1 ".b}, #12\n\t" "ext z" #A1 ".b, {z" #V1 ".b, z" #V2 ".b}, #12\n\t" \
    OPA(0, A0, B0) OPA(1, A1, B0) OPA(2, A0, B1) OPA(3, A1, B1)
    case 20:
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEPY(xa0, xb0, 8, 9, 10, 0, 1, 4, 5) STEPY(xa1, xb1, 16, 17, 18, 24, 25, 28, 29)
                     STEPY(xa2, xb2, 8, 9, 10, 0, 1, 4, 5) STEPY(xa3, xb3, 16, 17, 18, 24, 25, 28, 29)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    case 21: // 仅 16 ext（吞吐）
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     "ext z0.b, {z8.b, z9.b}, #12\n\t ext z1.b, {z9.b, z10.b}, #12\n\t ext z2.b, {z10.b, z11.b}, #12\n\t ext z3.b, {z11.b, z12.b}, #12\n\t"
                     "ext z4.b, {z8.b, z9.b}, #12\n\t ext z5.b, {z9.b, z10.b}, #12\n\t ext z6.b, {z10.b, z11.b}, #12\n\t ext z7.b, {z11.b, z12.b}, #12\n\t"
                     "ext z16.b, {z8.b, z9.b}, #12\n\t ext z17.b, {z9.b, z10.b}, #12\n\t ext z18.b, {z10.b, z11.b}, #12\n\t ext z19.b, {z11.b, z12.b}, #12\n\t"
                     "ext z20.b, {z8.b, z9.b}, #12\n\t ext z21.b, {z9.b, z10.b}, #12\n\t ext z22.b, {z10.b, z11.b}, #12\n\t ext z23.b, {z11.b, z12.b}, #12\n\t"
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : : "memory", "cc", VCLOB);
        break;
    // 1×4+ext + 8 条索引 fmla/步（第 5 行方案的完整形态）：5 a 对齐 + 1 b + 1 ld1rqw + 4 ext + 4 fmopa + 8 fmla
#define STEPXF(xa, xb, V0, V1, V2, V3, V4, A0, A1, A2, A3, B, K) \
    "ld1w {z" #V0 ".s}, p0/z, [%[" #xa "]]\n\t" "ld1w {z" #V1 ".s}, p0/z, [%[" #xa "], #1, mul vl]\n\t" \
    "ld1w {z" #V2 ".s}, p0/z, [%[" #xa "], #2, mul vl]\n\t" "ld1w {z" #V3 ".s}, p0/z, [%[" #xa "], #3, mul vl]\n\t" \
    "ld1w {z" #V4 ".s}, p0/z, [%[" #xa "], #4, mul vl]\n\t" LDB(B, xb) \
    "ld1rqw {z" #K ".s}, p0/z, [%[" #xb "], #16]\n\t" \
    "ext z" #A0 ".b, {z" #V0 ".b, z" #V1 ".b}, #12\n\t" "ext z" #A1 ".b, {z" #V1 ".b, z" #V2 ".b}, #12\n\t" \
    "ext z" #A2 ".b, {z" #V2 ".b, z" #V3 ".b}, #12\n\t" "ext z" #A3 ".b, {z" #V3 ".b, z" #V4 ".b}, #12\n\t" \
    OPA(0, A0, B) "fmla z24.s, z" #A0 ".s, z" #K ".s[0]\n\t fmla z25.s, z" #A0 ".s, z" #K ".s[1]\n\t" \
    OPA(1, A1, B) "fmla z26.s, z" #A0 ".s, z" #K ".s[2]\n\t fmla z27.s, z" #A0 ".s, z" #K ".s[3]\n\t" \
    OPA(2, A2, B) "fmla z28.s, z" #A1 ".s, z" #K ".s[0]\n\t fmla z29.s, z" #A1 ".s, z" #K ".s[1]\n\t" \
    OPA(3, A3, B) "fmla z30.s, z" #A1 ".s, z" #K ".s[2]\n\t fmla z31.s, z" #A1 ".s, z" #K ".s[3]\n\t"
    case 22:
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEPXF(xa0, xb0, 8, 9, 10, 11, 12, 0, 1, 2, 3, 4, 5) STEPXF(xa1, xb1, 16, 17, 18, 19, 20, 21, 22, 23, 13, 14, 6)
                     STEPXF(xa2, xb2, 8, 9, 10, 11, 12, 0, 1, 2, 3, 4, 5) STEPXF(xa3, xb3, 16, 17, 18, 19, 20, 21, 22, 23, 13, 14, 6)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    // 同上但每步 4 条 fmla
#define STEPXG(xa, xb, V0, V1, V2, V3, V4, A0, A1, A2, A3, B, K) \
    "ld1w {z" #V0 ".s}, p0/z, [%[" #xa "]]\n\t" "ld1w {z" #V1 ".s}, p0/z, [%[" #xa "], #1, mul vl]\n\t" \
    "ld1w {z" #V2 ".s}, p0/z, [%[" #xa "], #2, mul vl]\n\t" "ld1w {z" #V3 ".s}, p0/z, [%[" #xa "], #3, mul vl]\n\t" \
    "ld1w {z" #V4 ".s}, p0/z, [%[" #xa "], #4, mul vl]\n\t" LDB(B, xb) \
    "ld1rqw {z" #K ".s}, p0/z, [%[" #xb "], #16]\n\t" \
    "ext z" #A0 ".b, {z" #V0 ".b, z" #V1 ".b}, #12\n\t" "ext z" #A1 ".b, {z" #V1 ".b, z" #V2 ".b}, #12\n\t" \
    "ext z" #A2 ".b, {z" #V2 ".b, z" #V3 ".b}, #12\n\t" "ext z" #A3 ".b, {z" #V3 ".b, z" #V4 ".b}, #12\n\t" \
    OPA(0, A0, B) "fmla z24.s, z" #A0 ".s, z" #K ".s[0]\n\t" \
    OPA(1, A1, B) "fmla z25.s, z" #A0 ".s, z" #K ".s[1]\n\t" \
    OPA(2, A2, B) "fmla z26.s, z" #A0 ".s, z" #K ".s[2]\n\t" \
    OPA(3, A3, B) "fmla z27.s, z" #A0 ".s, z" #K ".s[3]\n\t"
    case 23:
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEPXG(xa0, xb0, 8, 9, 10, 11, 12, 0, 1, 2, 3, 4, 5) STEPXG(xa1, xb1, 16, 17, 18, 19, 20, 21, 22, 23, 13, 14, 6)
                     STEPXG(xa2, xb2, 8, 9, 10, 11, 12, 0, 1, 2, 3, 4, 5) STEPXG(xa3, xb3, 16, 17, 18, 19, 20, 21, 22, 23, 13, 14, 6)
                     "subs %0, %0, #1\n\t b.ne 1b\n\t"
                     : "+r"(n) : [xa0] "r"(xa0), [xa1] "r"(xa1), [xa2] "r"(xa2), [xa3] "r"(xa3),
                       [xb0] "r"(xb0), [xb1] "r"(xb1), [xb2] "r"(xb2), [xb3] "r"(xb3) : "memory", "cc", VCLOB);
        break;
    }
    return now() - t0;
}

int main(int argc, char** argv)
{
    int only = argc > 1 ? atoi(argv[1]) : -1;
    double ghz = argc > 2 ? atof(argv[2]) : 1.55;
    setvbuf(stdout, NULL, _IONBF, 0);
    float* a = aligned_alloc(256, 1 << 16);
    float* b = aligned_alloc(256, 1 << 16);
    memset(a, 0, 1 << 16);
    memset(b, 0, 1 << 16);
    long iters = 5000000;
    struct { int mode; long aoff, boff; const char* name; int nopa, nfmla; } T[] = {
        {0, 0, 0, "4 fmopa.s 轮转 4 tile", 4, 0},
        {1, 0, 0, "4 fmopa.s 同一 tile（延迟）", 4, 0},
        {2, 0, 0, "4 fmopa.s 两 tile 交替", 4, 0},
        {3, 0, 0, "16 fmopa + 20 ld1w 全对齐", 16, 0},
        {3, 1, 4, "16 fmopa + 20 ld1w  a+4B b+16B", 16, 0},
        {3, 8, 8, "16 fmopa + 20 ld1w  a+32B b+32B", 16, 0},
        {3, 1, 0, "16 fmopa + 20 ld1w  a+4B b 对齐", 16, 0},
        {3, 0, 4, "16 fmopa + 20 ld1w  a 对齐 b+16B", 16, 0},
        {4, 0, 0, "仅 20 ld1w 对齐", 0, 0},
        {4, 1, 4, "仅 20 ld1w a+4B b+16B", 0, 0},
        {5, 0, 0, "仅 4 ld4w 对齐", 0, 0},
        {5, 1, 0, "仅 4 ld4w +4B", 0, 0},
        {6, 0, 0, "16 fmopa + 4 ld4w 对齐 + 4 ld1w", 16, 0},
        {6, 1, 4, "16 fmopa + 4 ld4w +4B + 4 ld1w +16B", 16, 0},
        {7, 0, 0, "16 fmla.s（流式）", 0, 16},
        {8, 0, 0, "16 fmopa + 16 fmla.s 交错", 16, 16},
        {9, 0, 0, "16 fmopa + 32 fmla.s", 16, 32},
        {10, 0, 0, "16 fmopa + 64 fmla.s 索引", 16, 64},
        {11, 0, 0, "16 fmopa + 64 fmla idx + 24 ld 对齐", 16, 64},
        {11, 1, 4, "16 fmopa + 64 fmla idx + 24 ld 非对齐", 16, 64},
        {12, 1, 4, "16 fmopa + 32 fmla idx + 24 ld 非对齐", 16, 32},
        {13, 1, 4, "16 fmopa + 20 ld 非对齐 + 20 prfm", 16, 0},
        {14, 1, 4, "16 fmopa + 20 ld 非对齐 + 5 prfm", 16, 0},
        {15, 1, 4, "2x2: 16 fmopa + 8a(+4B) + 8b(+16B)", 16, 0},
        {16, 1, 4, "2x2 + 8 prfm", 16, 0},
        {17, 1, 0, "4x1: 16 fmopa + 4a(+4B) + 16b 对齐", 16, 0},
        {17, 1, 4, "4x1: 16 fmopa + 4a(+4B) + 16b(+16B)", 16, 0},
        {17, 1, 8, "4x1: 16 fmopa + 4a(+4B) + 16b(+32B)", 16, 0},
        {18, 1, 0, "仅 20 ld: a+4B b 对齐", 0, 0},
        {18, 8, 0, "仅 20 ld: a+32B b 对齐", 0, 0},
        {18, 0, 4, "仅 20 ld: a 对齐 b+16B", 0, 0},
        {19, 0, 4, "1x4+ext: 16 fmopa + 20a对齐 + 4b(+16B) + 16 ext", 16, 0},
        {20, 0, 4, "2x2+ext: 16 fmopa + 12a对齐 + 8b(+16B) + 8 ext", 16, 0},
        {21, 0, 0, "仅 16 ext", 0, 0},
        {22, 0, 4, "1x4+ext + 8 fmla/步 (32 fmla)", 16, 32},
        {23, 0, 4, "1x4+ext + 4 fmla/步 (16 fmla)", 16, 16},
    };
    int nT = sizeof(T) / sizeof(T[0]);
    asm volatile("smstart\n\t" ::: "memory", VCLOB);
    asm volatile("zero {za}\n\t" ::: "memory");
    for (int m = 0; m < nT; m++) {
        if (only >= 0 && m != only) continue;
        run(T[m].mode, iters / 10, a, b, T[m].aoff, T[m].boff);
        double t = run(T[m].mode, iters, a, b, T[m].aoff, T[m].boff);
        double cyc = t * ghz * 1e9 / iters;
        double flop = T[m].nopa * 512.0 + T[m].nfmla * 32.0;
        printf("  [%2d] %-40s %7.2f 周期/迭代  %7.1f GFLOPS/核\n", m, T[m].name, cyc, flop * iters / t * 1e-9);
    }
    asm volatile("smstop\n\t" ::: "memory", VCLOB);
    return 0;
}
