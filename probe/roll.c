// 滚动 16×1 形态探针：tile 行 ↔ 连续 16 个输入列，tile 列 c ↔ 输出行残差 (s+c) mod KH（每列一条独立的 fma 链，
// 链结束时 mova 竖切片出来直接 st1w 连续 16 float，再把该列清零开始下一行）。步数 = KW（无 X 方向浪费），
// 无 pass 边界。A/B 两组（残差 0..15 / 16..31）共用同一 a（32 列条带），各自 b。
// gcc -O3 -march=armv9-a+sme+sve2 -fopenmp roll.c -o roll -lm
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <sys/mman.h>

#define VCLOB "z0","z1","z2","z3","z4","z5","z6","z7","z8","z9","z10","z11","z12","z13","z14","z15","z16","z17","z18","z19","z20","z21","z22","z23","z24","z25","z26","z27","z28","z29","z30","z31"
#define PCLOB "p0","p1","p2","p3","p4","p5","p6","p7","p8","p9","p10","p11","p12","p13","p14","p15"
#define SMSTART() asm volatile("smstart" ::: "memory", VCLOB, PCLOB)
#define SMSTOP() asm volatile("smstop" ::: "memory", VCLOB, PCLOB)
static inline uint64_t cyc(void) { uint64_t v; asm volatile("mrs %0, cntvct_el0" : "=r"(v)); return v; }
static inline uint64_t cfrq(void) { uint64_t v; asm volatile("mrs %0, cntfrq_el0" : "=r"(v)); return v; }
static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + ts.tv_nsec * 1e-9; }
static void* alloc_big(size_t n) { void* p = NULL; if (posix_memalign(&p, 1 << 21, (n + (1 << 21) - 1) & ~((size_t)(1 << 21) - 1))) abort(); madvise(p, n, MADV_HUGEPAGE); return p; }

// 条带内核：32 列（2 tile）× 两组；行循环 + 步循环全在 asm 内。
//  in_row: 首行地址 (in + ja*W + col0)，rsb: 行距字节；R: b 表 [KH][KW][16]；RSB = KW*64；
//  nrows: 处理的输入行数；out_row0: 输出行 (ja-KH+1) 的地址（可能越界，前 KH-1 行用 scratch）；
//  cA0/cB0: 事件列计数初值；yA0/yB0: b 表行初值；mode: 1 带切换，0 不带（只量 fmopa+载入）。
static void strip_kernel(const float* in_row, long rsb, const float* R, long RSB, long KH, long KW, long nrows,
                         float* out_row0, float* scratch, long cA0, long cB0, long yA0, long yB0, int mode)
{
    const float* Rend = R + KH * RSB / 4;
    const float* bA = R + yA0 * RSB / 4;
    const float* bB = R + yB0 * RSB / 4;
    long valid_after = KH - 1;     // Y ≥ KH-1 时输出行有效
    if (mode) {
    asm volatile(
        "ptrue p0.s\n\t"
        "fmov z31.s, #0.0\n\t"
        "mov x17, %[cA0]\n\t"
        "mov x19, %[cB0]\n\t"
        "mov x0, %[in]\n\t"
        "mov x2, %[bA]\n\t"
        "mov x3, %[bB]\n\t"
        "mov x9, %[out]\n\t"
        "mov x8, %[nrows]\n\t"
        "mov x11, #0\n\t"                       // Y
        "1:\n\t"
        "mov x15, %[KW]\n\t"
        "mov x16, x0\n\t"
        "2:\n\t"
        "ld1w {z0.s}, p0/z, [x16]\n\t"
        "ld1w {z1.s}, p0/z, [x16, #1, mul vl]\n\t"
        "ld1w {z2.s}, p0/z, [x2]\n\t"
        "ld1w {z3.s}, p0/z, [x3]\n\t"
        "fmopa za0.s, p0/m, p0/m, z0.s, z2.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z1.s, z2.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z0.s, z3.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z1.s, z3.s\n\t"
        "add x16, x16, #4\n\t"
        "add x2, x2, #64\n\t"
        "add x3, x3, #64\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        // b 表回绕
        "cmp x2, %[Rend]\n\t"
        "csel x2, %[R], x2, eq\n\t"
        "cmp x3, %[Rend]\n\t"
        "csel x3, %[R], x3, eq\n\t"
        // 输出行指针：Y < KH-1 → scratch
        "cmp x11, %[va]\n\t"
        "csel x20, x9, %[scr], hs\n\t"
        // A 组切换（列 cA，事件 iff cA < 16）
        "and w12, w17, #15\n\t"
        "cmp x17, #16\n\t"
        "cset x18, lo\n\t"
        "dup z10.s, w18\n\t"
        "cmpne p1.s, p0/z, z10.s, #0\n\t"
        "mova z8.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za1v.s[w12, 0]\n\t"
        "st1w {z8.s}, p1, [x20]\n\t"
        "st1w {z9.s}, p1, [x20, #1, mul vl]\n\t"
        "mova za0v.s[w12, 0], p1/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p1/m, z31.s\n\t"
        // B 组切换
        "and w13, w19, #15\n\t"
        "cmp x19, #16\n\t"
        "cset x18, lo\n\t"
        "dup z10.s, w18\n\t"
        "cmpne p2.s, p0/z, z10.s, #0\n\t"
        "mova z8.s, p0/m, za2v.s[w13, 0]\n\t"
        "mova z9.s, p0/m, za3v.s[w13, 0]\n\t"
        "st1w {z8.s}, p2, [x20]\n\t"
        "st1w {z9.s}, p2, [x20, #1, mul vl]\n\t"
        "mova za2v.s[w13, 0], p2/m, z31.s\n\t"
        "mova za3v.s[w13, 0], p2/m, z31.s\n\t"
        // 计数推进
        "add x17, x17, #1\n\t"
        "cmp x17, %[KH]\n\t"
        "csel x17, xzr, x17, eq\n\t"
        "add x19, x19, #1\n\t"
        "cmp x19, %[KH]\n\t"
        "csel x19, xzr, x19, eq\n\t"
        "add x0, x0, %[rsb]\n\t"
        "add x9, x9, %[rsb]\n\t"
        "add x11, x11, #1\n\t"
        "subs x8, x8, #1\n\t"
        "b.ne 1b\n\t"
        :
        : [in]"r"(in_row), [rsb]"r"(rsb), [R]"r"(R), [Rend]"r"(Rend), [bA]"r"(bA), [bB]"r"(bB), [KH]"r"(KH), [KW]"r"(KW),
          [nrows]"r"(nrows), [out]"r"(out_row0), [scr]"r"(scratch), [cA0]"r"(cA0), [cB0]"r"(cB0), [va]"r"(valid_after)
        : "x0", "x2", "x3", "x8", "x9", "x11", "x12", "x13", "x15", "x16", "x17", "x18", "x19", "x20",
          "z0", "z1", "z2", "z3", "z8", "z9", "z10", "z31", "p0", "p1", "p2", "memory", "cc");
    } else {
    asm volatile(
        "ptrue p0.s\n\t"
        "mov x0, %[in]\n\t"
        "mov x2, %[bA]\n\t"
        "mov x3, %[bB]\n\t"
        "mov x8, %[nrows]\n\t"
        "1:\n\t"
        "mov x15, %[KW]\n\t"
        "mov x16, x0\n\t"
        "2:\n\t"
        "ld1w {z0.s}, p0/z, [x16]\n\t"
        "ld1w {z1.s}, p0/z, [x16, #1, mul vl]\n\t"
        "ld1w {z2.s}, p0/z, [x2]\n\t"
        "ld1w {z3.s}, p0/z, [x3]\n\t"
        "fmopa za0.s, p0/m, p0/m, z0.s, z2.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z1.s, z2.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z0.s, z3.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z1.s, z3.s\n\t"
        "add x16, x16, #4\n\t"
        "add x2, x2, #64\n\t"
        "add x3, x3, #64\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        "cmp x2, %[Rend]\n\t"
        "csel x2, %[R], x2, eq\n\t"
        "cmp x3, %[Rend]\n\t"
        "csel x3, %[R], x3, eq\n\t"
        "add x0, x0, %[rsb]\n\t"
        "subs x8, x8, #1\n\t"
        "b.ne 1b\n\t"
        :
        : [in]"r"(in_row), [rsb]"r"(rsb), [R]"r"(R), [Rend]"r"(Rend), [bA]"r"(bA), [bB]"r"(bB), [KW]"r"(KW), [nrows]"r"(nrows)
        : "x0", "x2", "x3", "x8", "x15", "x16", "z0", "z1", "z2", "z3", "p0", "memory", "cc");
    }
}


// ---------- 8×2 tile（stride 2，4 tile = 128 列，一组 8 个残差 s_base..s_base+7，nvalid 个有效）----------
// R8[y][X][c], c = 2s+ic: k[(y-s) mod KH][X-ic]（越界/无效残差为 0）；步数 KW+1（偶数）
static void strip_kernel8(const float* in_row, long rsb, const float* R, long RSB, long KH, long steps, long nrows,
                          float* out_row0, float* scratch, long c0, long y0, long nvalid)
{
    const float* Rend = R + KH * RSB / 4;
    const float* b0 = R + y0 * RSB / 4;
    long valid_after = KH - 1, it = steps / 2;
    asm volatile(
        "ptrue p0.s\n\t"
        "fmov z31.s, #0.0\n\t"
        "mov x17, %[c0]\n\t"
        "mov x0, %[in]\n\t"
        "mov x2, %[b0]\n\t"
        "mov x9, %[out]\n\t"
        "mov x8, %[nrows]\n\t"
        "mov x11, #0\n\t"
        "1:\n\t"
        "mov x15, %[it]\n\t"
        "mov x16, x0\n\t"
        "2:\n\t"
        "ld2w {z0.s, z1.s}, p0/z, [x16]\n\t"
        "ld2w {z2.s, z3.s}, p0/z, [x16, #2, mul vl]\n\t"
        "ld2w {z4.s, z5.s}, p0/z, [x16, #4, mul vl]\n\t"
        "ld2w {z6.s, z7.s}, p0/z, [x16, #6, mul vl]\n\t"
        "ld1w {z8.s}, p0/z, [x2]\n\t"
        "ld1w {z9.s}, p0/z, [x2, #1, mul vl]\n\t"
        "fmopa za0.s, p0/m, p0/m, z0.s, z8.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z2.s, z8.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z4.s, z8.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z6.s, z8.s\n\t"
        "fmopa za0.s, p0/m, p0/m, z1.s, z9.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z3.s, z9.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z5.s, z9.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z7.s, z9.s\n\t"
        "add x16, x16, #8\n\t"
        "add x2, x2, #128\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        "cmp x2, %[Rend]\n\t"
        "csel x2, %[R], x2, eq\n\t"
        "cmp x11, %[va]\n\t"
        "csel x20, x9, %[scr], hs\n\t"
        // 事件：s = x17 < nvalid → 列 2s, 2s+1
        "and w12, w17, #7\n\t"
        "lsl w12, w12, #1\n\t"
        "cmp x17, %[nv]\n\t"
        "cset x18, lo\n\t"
        "dup z10.s, w18\n\t"
        "cmpne p1.s, p0/z, z10.s, #0\n\t"
        "mova z8.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za0v.s[w12, 1]\n\t"
        "mova z10.s, p0/m, za1v.s[w12, 0]\n\t"
        "mova z11.s, p0/m, za1v.s[w12, 1]\n\t"
        "mova z12.s, p0/m, za2v.s[w12, 0]\n\t"
        "mova z13.s, p0/m, za2v.s[w12, 1]\n\t"
        "mova z14.s, p0/m, za3v.s[w12, 0]\n\t"
        "mova z15.s, p0/m, za3v.s[w12, 1]\n\t"
        "st2w {z8.s, z9.s}, p1, [x20]\n\t"
        "st2w {z10.s, z11.s}, p1, [x20, #2, mul vl]\n\t"
        "st2w {z12.s, z13.s}, p1, [x20, #4, mul vl]\n\t"
        "st2w {z14.s, z15.s}, p1, [x20, #6, mul vl]\n\t"
        "mova za0v.s[w12, 0], p1/m, z31.s\n\t"
        "mova za0v.s[w12, 1], p1/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p1/m, z31.s\n\t"
        "mova za1v.s[w12, 1], p1/m, z31.s\n\t"
        "mova za2v.s[w12, 0], p1/m, z31.s\n\t"
        "mova za2v.s[w12, 1], p1/m, z31.s\n\t"
        "mova za3v.s[w12, 0], p1/m, z31.s\n\t"
        "mova za3v.s[w12, 1], p1/m, z31.s\n\t"
        "add x17, x17, #1\n\t"
        "cmp x17, %[KH]\n\t"
        "csel x17, xzr, x17, eq\n\t"
        "add x0, x0, %[rsb]\n\t"
        "add x9, x9, %[rsb]\n\t"
        "add x11, x11, #1\n\t"
        "subs x8, x8, #1\n\t"
        "b.ne 1b\n\t"
        :
        : [in]"r"(in_row), [rsb]"r"(rsb), [R]"r"(R), [Rend]"r"(Rend), [b0]"r"(b0), [KH]"r"(KH), [it]"r"(it),
          [nrows]"r"(nrows), [out]"r"(out_row0), [scr]"r"(scratch), [c0]"r"(c0), [va]"r"(valid_after), [nv]"r"(nvalid)
        : "x0", "x2", "x8", "x9", "x11", "x12", "x15", "x16", "x17", "x18", "x20",
          "z0", "z1", "z2", "z3", "z4", "z5", "z6", "z7", "z8", "z9", "z10", "z11", "z12", "z13", "z14", "z15", "z31", "p0", "p1", "memory", "cc");
}
static void build_R8(float* R, const float* k, long KH, long KW, long steps, long s_base)
{
    for (long y = 0; y < KH; y++)
        for (long X = 0; X < steps; X++)
            for (long c = 0; c < 16; c++) {
                long s = c >> 1, ic = c & 1, ki = X - ic;
                long kj = ((y - s) % KH + KH) % KH;
                R[(y * steps + X) * 16 + c] = (ki >= 0 && ki < KW && s_base + s < KH) ? k[kj * KW + ki] : 0.f;
            }
}

// ---------- 2×8 tile（stride 8，4 tile = 512 列，一组 2 个残差，nvalid 个有效）----------
// R2[y][X][c], c = 8s+ic: k[(y-s) mod KH][X-ic]；步数 pad 到 8 的倍数（多出的步 b=0）
static void strip_kernel2(const float* in_row, long rsb, const float* R, long RSB, long KH, long steps8, long nrows,
                          float* out_row0, float* scratch, long c0, long y0, long nvalid)
{
    const float* Rend = R + KH * RSB / 4;
    const float* b0 = R + y0 * RSB / 4;
    long valid_after = KH - 1, it = steps8 / 8;
    asm volatile(
        "ptrue p0.s\n\t"
        "fmov z31.s, #0.0\n\t"
        "mov x17, %[c0]\n\t"
        "mov x0, %[in]\n\t"
        "mov x2, %[b0]\n\t"
        "mov x9, %[out]\n\t"
        "mov x8, %[nrows]\n\t"
        "mov x11, #0\n\t"
        "1:\n\t"
        "mov x15, %[it]\n\t"
        "mov x16, x0\n\t"
        "2:\n\t"
        // tile0: [x16], [x16+64]; tile1: +128, +192; tile2: +256, +320; tile3: +384, +448 (floats)
        "ld4w {z0.s, z1.s, z2.s, z3.s}, p0/z, [x16]\n\t"
        "ld4w {z4.s, z5.s, z6.s, z7.s}, p0/z, [x16, #4, mul vl]\n\t"
        "uzp1 z16.s, z0.s, z4.s\n\t"    // a0(X)
        "uzp2 z20.s, z0.s, z4.s\n\t"    // a0(X+4)
        "uzp1 z17.s, z1.s, z5.s\n\t"    // a0(X+1)
        "uzp2 z21.s, z1.s, z5.s\n\t"    // a0(X+5)
        "uzp1 z18.s, z2.s, z6.s\n\t"
        "uzp2 z22.s, z2.s, z6.s\n\t"
        "uzp1 z19.s, z3.s, z7.s\n\t"
        "uzp2 z23.s, z3.s, z7.s\n\t"
        "ld1w {z8.s}, p0/z, [x2]\n\t"
        "ld1w {z9.s}, p0/z, [x2, #1, mul vl]\n\t"
        "ld1w {z10.s}, p0/z, [x2, #2, mul vl]\n\t"
        "ld1w {z11.s}, p0/z, [x2, #3, mul vl]\n\t"
        "ld1w {z12.s}, p0/z, [x2, #4, mul vl]\n\t"
        "ld1w {z13.s}, p0/z, [x2, #5, mul vl]\n\t"
        "ld1w {z14.s}, p0/z, [x2, #6, mul vl]\n\t"
        "ld1w {z15.s}, p0/z, [x2, #7, mul vl]\n\t"
        "fmopa za0.s, p0/m, p0/m, z16.s, z8.s\n\t"
        "ld4w {z0.s, z1.s, z2.s, z3.s}, p0/z, [x16, #8, mul vl]\n\t"
        "ld4w {z4.s, z5.s, z6.s, z7.s}, p0/z, [x16, #12, mul vl]\n\t"
        "fmopa za0.s, p0/m, p0/m, z17.s, z9.s\n\t"
        "uzp1 z24.s, z0.s, z4.s\n\t"    // a1(X)
        "uzp2 z28.s, z0.s, z4.s\n\t"
        "fmopa za0.s, p0/m, p0/m, z18.s, z10.s\n\t"
        "uzp1 z25.s, z1.s, z5.s\n\t"
        "uzp2 z29.s, z1.s, z5.s\n\t"
        "fmopa za0.s, p0/m, p0/m, z19.s, z11.s\n\t"
        "uzp1 z26.s, z2.s, z6.s\n\t"
        "uzp2 z30.s, z2.s, z6.s\n\t"
        "fmopa za0.s, p0/m, p0/m, z20.s, z12.s\n\t"
        "uzp1 z27.s, z3.s, z7.s\n\t"
        "uzp2 z16.s, z3.s, z7.s\n\t"    // a1(X+7)（z16 已用完）
        "fmopa za0.s, p0/m, p0/m, z21.s, z13.s\n\t"
        "ld4w {z0.s, z1.s, z2.s, z3.s}, p0/z, [x16, #16, mul vl]\n\t"
        "ld4w {z4.s, z5.s, z6.s, z7.s}, p0/z, [x16, #20, mul vl]\n\t"
        "fmopa za0.s, p0/m, p0/m, z22.s, z14.s\n\t"
        "fmopa za0.s, p0/m, p0/m, z23.s, z15.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z24.s, z8.s\n\t"
        "uzp1 z17.s, z0.s, z4.s\n\t"    // a2(X)
        "uzp2 z21.s, z0.s, z4.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z25.s, z9.s\n\t"
        "uzp1 z18.s, z1.s, z5.s\n\t"
        "uzp2 z22.s, z1.s, z5.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z26.s, z10.s\n\t"
        "uzp1 z19.s, z2.s, z6.s\n\t"
        "uzp2 z23.s, z2.s, z6.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z27.s, z11.s\n\t"
        "uzp1 z20.s, z3.s, z7.s\n\t"
        "uzp2 z24.s, z3.s, z7.s\n\t"    // a2(X+7)
        "fmopa za1.s, p0/m, p0/m, z28.s, z12.s\n\t"
        "ld4w {z0.s, z1.s, z2.s, z3.s}, p0/z, [x16, #24, mul vl]\n\t"
        "ld4w {z4.s, z5.s, z6.s, z7.s}, p0/z, [x16, #28, mul vl]\n\t"
        "fmopa za1.s, p0/m, p0/m, z29.s, z13.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z30.s, z14.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z16.s, z15.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z17.s, z8.s\n\t"
        "uzp1 z25.s, z0.s, z4.s\n\t"    // a3(X)
        "uzp2 z29.s, z0.s, z4.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z18.s, z9.s\n\t"
        "uzp1 z26.s, z1.s, z5.s\n\t"
        "uzp2 z30.s, z1.s, z5.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z19.s, z10.s\n\t"
        "uzp1 z27.s, z2.s, z6.s\n\t"
        "uzp2 z16.s, z2.s, z6.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z20.s, z11.s\n\t"
        "uzp1 z28.s, z3.s, z7.s\n\t"
        "uzp2 z17.s, z3.s, z7.s\n\t"    // a3(X+7)
        "fmopa za2.s, p0/m, p0/m, z21.s, z12.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z22.s, z13.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z23.s, z14.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z24.s, z15.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z25.s, z8.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z26.s, z9.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z27.s, z10.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z28.s, z11.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z29.s, z12.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z30.s, z13.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z16.s, z14.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z17.s, z15.s\n\t"
        "add x16, x16, #32\n\t"
        "add x2, x2, #512\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        "cmp x2, %[Rend]\n\t"
        "csel x2, %[R], x2, eq\n\t"
        "cmp x11, %[va]\n\t"
        "csel x20, x9, %[scr], hs\n\t"
        // 事件：s = x17 < nvalid → 列 8s..8s+7；每 tile 8 mova + 8 zip + 2 st4w
        "and w12, w17, #1\n\t"
        "lsl w12, w12, #3\n\t"
        "cmp x17, %[nv]\n\t"
        "cset x18, lo\n\t"
        "dup z10.s, w18\n\t"
        "cmpne p1.s, p0/z, z10.s, #0\n\t"
#define EX8(T, OFF) \
        "mova z0.s, p0/m, za" #T "v.s[w12, 0]\n\t" \
        "mova z1.s, p0/m, za" #T "v.s[w12, 1]\n\t" \
        "mova z2.s, p0/m, za" #T "v.s[w12, 2]\n\t" \
        "mova z3.s, p0/m, za" #T "v.s[w12, 3]\n\t" \
        "add w13, w12, #4\n\t" \
        "mova z4.s, p0/m, za" #T "v.s[w13, 0]\n\t" \
        "mova z5.s, p0/m, za" #T "v.s[w13, 1]\n\t" \
        "mova z6.s, p0/m, za" #T "v.s[w13, 2]\n\t" \
        "mova z7.s, p0/m, za" #T "v.s[w13, 3]\n\t" \
        "zip1 z16.s, z0.s, z4.s\n\t" "zip1 z17.s, z1.s, z5.s\n\t" "zip1 z18.s, z2.s, z6.s\n\t" "zip1 z19.s, z3.s, z7.s\n\t" \
        "zip2 z20.s, z0.s, z4.s\n\t" "zip2 z21.s, z1.s, z5.s\n\t" "zip2 z22.s, z2.s, z6.s\n\t" "zip2 z23.s, z3.s, z7.s\n\t" \
        "st4w {z16.s, z17.s, z18.s, z19.s}, p1, [x20, #" #OFF ", mul vl]\n\t" \
        "st4w {z20.s, z21.s, z22.s, z23.s}, p1, [x20, #" #OFF "+4, mul vl]\n\t" \
        "mova za" #T "v.s[w12, 0], p1/m, z31.s\n\t" "mova za" #T "v.s[w12, 1], p1/m, z31.s\n\t" \
        "mova za" #T "v.s[w12, 2], p1/m, z31.s\n\t" "mova za" #T "v.s[w12, 3], p1/m, z31.s\n\t" \
        "mova za" #T "v.s[w13, 0], p1/m, z31.s\n\t" "mova za" #T "v.s[w13, 1], p1/m, z31.s\n\t" \
        "mova za" #T "v.s[w13, 2], p1/m, z31.s\n\t" "mova za" #T "v.s[w13, 3], p1/m, z31.s\n\t"
        EX8(0, 0)
        EX8(1, 8)
        EX8(2, 16)
        EX8(3, 24)
#undef EX8
        "add x17, x17, #1\n\t"
        "cmp x17, %[KH]\n\t"
        "csel x17, xzr, x17, eq\n\t"
        "add x0, x0, %[rsb]\n\t"
        "add x9, x9, %[rsb]\n\t"
        "add x11, x11, #1\n\t"
        "subs x8, x8, #1\n\t"
        "b.ne 1b\n\t"
        :
        : [in]"r"(in_row), [rsb]"r"(rsb), [R]"r"(R), [Rend]"r"(Rend), [b0]"r"(b0), [KH]"r"(KH), [it]"r"(it),
          [nrows]"r"(nrows), [out]"r"(out_row0), [scr]"r"(scratch), [c0]"r"(c0), [va]"r"(valid_after), [nv]"r"(nvalid)
        : "x0", "x2", "x8", "x9", "x11", "x12", "x13", "x15", "x16", "x17", "x18", "x20", VCLOB, "p0", "p1", "memory", "cc");
}
static void build_R2(float* R, const float* k, long KH, long KW, long steps8, long s_base)
{
    for (long y = 0; y < KH; y++)
        for (long X = 0; X < steps8; X++)
            for (long c = 0; c < 16; c++) {
                long s = c >> 3, ic = c & 7, ki = X - ic;
                long kj = ((y - s) % KH + KH) % KH;
                R[(y * steps8 + X) * 16 + c] = (ki >= 0 && ki < KW && s_base + s < KH) ? k[kj * KW + ki] : 0.f;
            }
}

// R[y][X][c] = k[(y - c) mod KH][X]
static void build_R(float* R, const float* k, long KH, long KW)
{
    for (long y = 0; y < KH; y++)
        for (long X = 0; X < KW; X++)
            for (long c = 0; c < 16; c++) {
                long kj = ((y - c) % KH + KH) % KH;
                R[(y * KW + X) * 16 + c] = k[kj * KW + X];
            }
}

static float ref_out(const float* in, long W, const float* k, long KH, long KW, long j, long i)
{
    float acc = 0.f;
    for (long jk = 0; jk < KH; jk++)
        for (long ik = 0; ik < KW; ik++)
            acc = fmaf(in[(j + jk) * W + i + ik], k[jk * KW + ik], acc);
    return acc;
}

int main(int argc, char** argv)
{
    long H = argc > 1 ? atol(argv[1]) : 4096, W = argc > 2 ? atol(argv[2]) : 6144;
    long KH = argc > 3 ? atol(argv[3]) : 39, KW = argc > 4 ? atol(argv[4]) : KH;
    int nthr = argc > 5 ? atoi(argv[5]) : 1;
    long outH = H - KH + 1, outW = W - KW + 1;
    setvbuf(stdout, NULL, _IONBF, 0);
    float* in = alloc_big((size_t)H * W * 4);
    float* out = alloc_big((size_t)H * W * 4);
    float* k = malloc(KH * KW * 4);
    srand(1);
    for (long i = 0; i < H * W; i++) in[i] = (float)rand() / RAND_MAX;
    for (long i = 0; i < KH * KW; i++) k[i] = (float)rand() / RAND_MAX;
    for (long i = 0; i < H * W; i++) out[i] = NAN;
    long RSB = KW * 64;
    float* R = alloc_big((size_t)KH * RSB);
    build_R(R, k, KH, KW);
    float* scratch = alloc_big(1 << 16);
    const double ghz = 1.55;
    printf("H=%ld W=%ld KH=%ld KW=%ld threads=%d  cntfrq=%lu\n", H, W, KH, KW, nthr, cfrq());

    // 正确性：一个条带（col0=64），全高
    {
        long col0 = 64, nrows = H;
        SMSTART();
        asm volatile("zero {za}" ::: "memory");
        strip_kernel(in + col0, W * 4, R, RSB, KH, KW, nrows, out + (-(KH - 1)) * W + col0, scratch,
                     (1) % KH, ((1 - 16) % KH + KH) % KH, 0, (KH - 16) % KH, 1);
        SMSTOP();
        long bad = 0, chk = 0;
        for (long j = 0; j < outH; j++) {
            if (j % KH >= 32) continue;             // 本探针只算残差 0..31
            for (long i = col0; i < col0 + 32; i++) {
                float r = ref_out(in, W, k, KH, KW, j, i), o = out[j * W + i];
                chk++;
                if (memcmp(&r, &o, 4) != 0) { if (bad < 5) printf("  mismatch j=%ld i=%ld ref=%.8g got=%.8g\n", j, i, r, o); bad++; }
            }
        }
        printf("correctness: %ld checked, %ld mismatches %s\n", chk, bad, bad ? "FAIL" : "PASS(bit-exact)");
    }

    // 计时：单线程，行距 0（同一行，L1 驻留） / 真实行距（DRAM 流）；带切换 / 不带
    for (int mode = 0; mode <= 1; mode++)
        for (int real = 0; real <= 1; real++) {
            long nrows = H, col0 = 64;
            SMSTART();
            asm volatile("zero {za}" ::: "memory");
            double best = 1e9;
            for (int rep = 0; rep < 3; rep++) {
                uint64_t c0 = cyc();
                strip_kernel(in + col0, real ? W * 4 : 0, R, RSB, KH, KW, nrows, real ? out + (-(KH - 1)) * W + col0 : scratch + 4096, scratch,
                             1 % KH, ((1 - 16) % KH + KH) % KH, 0, (KH - 16) % KH, mode);
                uint64_t c1 = cyc();
                double t = (double)(c1 - c0) / cfrq();
                if (t < best) best = t;
            }
            SMSTOP();
            double cps = best * ghz * 1e9 / (nrows * KW);
            printf("  single: %s %s: %.3f ms  %.3f 周期/步 (理想 8)  效率 %.1f%%\n", mode ? "带切换" : "无切换", real ? "真实行距(DRAM)" : "行距0(L1)",
                   best * 1e3, cps, 800.0 / cps);
        }


    // 8×2：残差 s_base=32（k39: 32..38 有效 7 个；k41: 32..39 8 个；k55: 48..54；k81: 80）
    {
        long s_base = (KH / 16) * 16, nvalid = KH - s_base; if (nvalid > 8) nvalid = 8;
        long steps = KW + 1; if (steps & 1) steps++;
        long RSB8 = steps * 64;
        float* R8 = alloc_big((size_t)KH * RSB8);
        build_R8(R8, k, KH, KW, steps, s_base);
        long col0 = 128, nrows = H;
        for (long i = 0; i < H * W; i++) out[i] = NAN;
        SMSTART(); asm volatile("zero {za}" ::: "memory");
        strip_kernel8(in + col0, W * 4, R8, RSB8, KH, steps, nrows, out + (-(KH - 1)) * W + col0, scratch,
                      (1 - 0) % KH, ((0 - s_base) % KH + KH) % KH, nvalid);
        SMSTOP();
        long bad = 0, chk = 0;
        for (long j = 0; j < outH; j++) {
            long r = j % KH; if (r < s_base || r >= s_base + nvalid) continue;
            for (long i = col0; i < col0 + 128; i++) {
                float rf = ref_out(in, W, k, KH, KW, j, i), o = out[j * W + i]; chk++;
                if (memcmp(&rf, &o, 4) != 0) { if (bad < 5) printf("  8x2 mismatch j=%ld i=%ld ref=%.8g got=%.8g\n", j, i, rf, o); bad++; }
            }
        }
        printf("8x2 correctness (s_base %ld, nvalid %ld): %ld checked, %ld mismatches %s\n", s_base, nvalid, chk, bad, bad ? "FAIL" : "PASS");
        for (int real = 0; real <= 1; real++) {
            SMSTART(); asm volatile("zero {za}" ::: "memory");
            double best = 1e9;
            for (int rep = 0; rep < 3; rep++) {
                uint64_t c0 = cyc();
                strip_kernel8(in + col0, real ? W * 4 : 0, R8, RSB8, KH, steps, nrows, real ? out + (-(KH - 1)) * W + col0 : scratch + 4096, scratch,
                              1 % KH, ((0 - s_base) % KH + KH) % KH, nvalid);
                double t = (double)(cyc() - c0) / cfrq(); if (t < best) best = t;
            }
            SMSTOP();
            double cps = best * ghz * 1e9 / (nrows * steps);
            printf("  8x2 single %s: %.3f ms  %.3f 周期/步 (理想 8)  效率 %.1f%%\n", real ? "DRAM" : "L1", best * 1e3, cps, 800.0 / cps);
        }
        free(R8);
    }
    // 2×8：残差 s_base = 最后 1–2 个（k41: 40；k81: 80；k39: 37,38 用来测正确性）
    {
        long s_base = KH - 2, nvalid = 2;
        long steps8 = (KW + 7 + 7) & ~7L;
        long RSB2 = steps8 * 64;
        float* R2 = alloc_big((size_t)KH * RSB2);
        build_R2(R2, k, KH, KW, steps8, s_base);
        long col0 = 512, nrows = H;
        for (long i = 0; i < H * W; i++) out[i] = NAN;
        SMSTART(); asm volatile("zero {za}" ::: "memory");
        strip_kernel2(in + col0, W * 4, R2, RSB2, KH, steps8, nrows, out + (-(KH - 1)) * W + col0, scratch,
                      1 % KH, ((0 - s_base) % KH + KH) % KH, nvalid);
        SMSTOP();
        long bad = 0, chk = 0;
        for (long j = 0; j < outH; j++) {
            long r = j % KH; if (r < s_base || r >= s_base + nvalid) continue;
            for (long i = col0; i < col0 + 512; i++) {
                float rf = ref_out(in, W, k, KH, KW, j, i), o = out[j * W + i]; chk++;
                if (memcmp(&rf, &o, 4) != 0) { if (bad < 5) printf("  2x8 mismatch j=%ld i=%ld ref=%.8g got=%.8g\n", j, i, rf, o); bad++; }
            }
        }
        printf("2x8 correctness (s_base %ld): %ld checked, %ld mismatches %s\n", s_base, chk, bad, bad ? "FAIL" : "PASS");
        for (int real = 0; real <= 1; real++) {
            SMSTART(); asm volatile("zero {za}" ::: "memory");
            double best = 1e9;
            for (int rep = 0; rep < 3; rep++) {
                uint64_t c0 = cyc();
                strip_kernel2(in + col0, real ? W * 4 : 0, R2, RSB2, KH, steps8, nrows, real ? out + (-(KH - 1)) * W + col0 : scratch + 4096, scratch,
                              1 % KH, ((0 - s_base) % KH + KH) % KH, nvalid);
                double t = (double)(cyc() - c0) / cfrq(); if (t < best) best = t;
            }
            SMSTOP();
            double cps = best * ghz * 1e9 / (nrows * steps8);
            printf("  2x8 single %s: %.3f ms  %.3f 周期/步 (理想 8)  效率 %.1f%%（步数 pad %ld，真实 %ld）\n", real ? "DRAM" : "L1", best * 1e3, cps, 800.0 / cps, steps8, KW + 7);
        }
        free(R2);
    }

    // 多线程：每线程一个条带序列（col0 = 32*(t + n*nthr)），真实行距，带切换 → 看 DRAM/L3 争用
    if (nthr > 1) {
        long nstrips = outW / 32;
        double* thr_cps = calloc(nthr, sizeof(double));
        double t0 = now();
        #pragma omp parallel num_threads(nthr)
        {
            int t = omp_get_thread_num();
            SMSTART();
            uint64_t tot = 0; long steps = 0;
            for (long s = t; s < nstrips; s += nthr) {
                long col0 = s * 32;
                asm volatile("zero {za}" ::: "memory");
                uint64_t c0 = cyc();
                strip_kernel(in + col0, W * 4, R, RSB, KH, KW, H, out + (-(KH - 1)) * W + col0, scratch + 8192 + t * 64,
                             1 % KH, ((1 - 16) % KH + KH) % KH, 0, (KH - 16) % KH, 1);
                tot += cyc() - c0; steps += H * KW;
            }
            SMSTOP();
            thr_cps[t] = (double)tot / cfrq() * ghz * 1e9 / steps;
        }
        double t1 = now() - t0;
        double mn = 1e9, mx = 0, av = 0;
        for (int t = 0; t < nthr; t++) { if (thr_cps[t] < mn) mn = thr_cps[t]; if (thr_cps[t] > mx) mx = thr_cps[t]; av += thr_cps[t] / nthr; }
        double flops = 2.0 * outH * outW * KH * KW * (32.0 / KH);   // 只算了残差 0..31 的行
        printf("  %d 线程 A+B 全图: 周期/步 min %.3f avg %.3f max %.3f  (理想 8)  墙钟 %.2f ms  等效 %.0f GFLOPS（对 32/%ld 的行）\n",
               nthr, mn, av, mx, t1 * 1e3, flops / t1 * 1e-9, KH);
    }
    return 0;
}
