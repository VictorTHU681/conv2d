// 滚动形态原型（全流程）：16×1 对（A/B 两组共用 32 列 a）、16×1 单（4 tile 64 列）、8×2（ld2w，4 tile 128 列）、
// 2×8（ld2w+两级 uzp，4 tile 512 列）；按 KH 分解残差组；38 线程按 (item, 输出行) 静态等分；软件预取 PD 行。
// gcc -O3 -march=armv9-a+sme+sve2 -fopenmp roll2.c -o roll2 -lm
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <sched.h>
#include <sys/mman.h>

#define VCLOB "z0","z1","z2","z3","z4","z5","z6","z7","z8","z9","z10","z11","z12","z13","z14","z15","z16","z17","z18","z19","z20","z21","z22","z23","z24","z25","z26","z27","z28","z29","z30","z31"
#define PCLOB "p0","p1","p2","p3","p4","p5","p6","p7","p8","p9","p10","p11","p12","p13","p14","p15"
#define SMSTART() asm volatile("smstart" ::: "memory", VCLOB, PCLOB)
#define SMSTOP() asm volatile("smstop" ::: "memory", VCLOB, PCLOB)
static inline uint64_t cyc(void) { uint64_t v; asm volatile("mrs %0, cntvct_el0" : "=r"(v)); return v; }
static inline uint64_t cfrq(void) { uint64_t v; asm volatile("mrs %0, cntfrq_el0" : "=r"(v)); return v; }
static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + ts.tv_nsec * 1e-9; }
static void* alloc_big(size_t n) { void* p = NULL; if (posix_memalign(&p, 1 << 21, (n + (1 << 21) - 1) & ~((size_t)(1 << 21) - 1))) abort(); madvise(p, n, MADV_HUGEPAGE); return p; }
static long PD = 3;   // 预取提前行数

// 内核参数（asm 内从结构体装载，避免操作数过多）
//  行数据先由 prfm pldl2keep 提前 PD 行进 L2，再在处理第 Y 行时把第 Y+1 行的段拷进 L1 环（2 槽），a 从环取：
//  避免行距 16/24 KB 与 L1 组混叠（每行落在同一组，PD 行同时在 L1 会互相逐出）。
typedef struct {
    int64_t in_row, rsb, R, Rend, bA, bB, KH, steps, nrows, out, scr, cA0, cB0, va, nvA, nvB, pf, it, PD, ring, slot, ncp_full, ncp_tail;
} ka_t;
typedef struct {
    const float* in_row; long rsb; const float* R; long RSB; long KH, steps, nrows;
    float* out_row0; float* scratch; long cA0, cB0, yA0, yB0, nvA, nvB; float* ring; long KW;
} kp_t;
static void fill_args(ka_t* A, const kp_t* P, long div, long slot, long ncp)
{
    A->ncp_full = ncp / 16; A->ncp_tail = ncp % 16;
    A->in_row = (int64_t)P->in_row; A->rsb = P->rsb; A->R = (int64_t)P->R; A->Rend = (int64_t)(P->R + P->KH * P->RSB / 4);
    A->bA = (int64_t)(P->R + P->yA0 * P->RSB / 4); A->bB = (int64_t)(P->R + P->yB0 * P->RSB / 4);
    A->KH = P->KH; A->steps = P->steps; A->nrows = P->nrows; A->out = (int64_t)P->out_row0; A->scr = (int64_t)P->scratch;
    A->cA0 = P->cA0; A->cB0 = P->cB0; A->va = P->KH - 1; A->nvA = P->nvA; A->nvB = P->nvB; A->pf = PD * P->rsb; A->it = P->steps / div; A->PD = PD;
    A->ring = (int64_t)P->ring; A->slot = slot;
    memcpy(P->ring, P->in_row, ncp * 4);     // 第 0 行进槽 0
}
// 寄存器约定：x0 行指针(输入) x1 rsb x2 bA x3 bB x4 R x5 Rend x6 KH x7 steps/it x8 行计数 x9 out 行 x10 scr x11 Y x12/x13 切片号
//  x14 va x15 步计数 x16 a 指针(环槽) x17 环槽当前 x19 cB x20 out/scr 选择 x21 预取地址 x22/x23 临时 x24 nvA x25 nvB x26 pf x27 cA x28 环基址
#define LOAD_ARGS \
        "ldr x0, [%[A], #0]\n\t" "ldr x1, [%[A], #8]\n\t" "ldr x4, [%[A], #16]\n\t" "ldr x5, [%[A], #24]\n\t" \
        "ldr x2, [%[A], #32]\n\t" "ldr x3, [%[A], #40]\n\t" "ldr x6, [%[A], #48]\n\t" "ldr x7, [%[A], #56]\n\t" \
        "ldr x8, [%[A], #64]\n\t" "ldr x9, [%[A], #72]\n\t" "ldr x10, [%[A], #80]\n\t" "ldr x27, [%[A], #88]\n\t" \
        "ldr x19, [%[A], #96]\n\t" "ldr x14, [%[A], #104]\n\t" "ldr x24, [%[A], #112]\n\t" "ldr x25, [%[A], #120]\n\t" \
        "ldr x26, [%[A], #128]\n\t" "ldr x17, [%[A], #152]\n\t" "ldr x22, [%[A], #160]\n\t" "add x28, x17, x17\n\t" "add x28, x28, x22\n\t" \
        "ldr x22, [%[A], #176]\n\t" "whilelo p3.s, xzr, x22\n\t" "mov x11, #0\n\t" "ptrue p0.s\n\t"
#define XCLOB "x0","x1","x2","x3","x4","x5","x6","x7","x8","x9","x10","x11","x12","x13","x14","x15","x16","x17","x19","x20","x21","x22","x23","x24","x25","x26","x27","x28"
#define ROW_TAIL \
        "add x0, x0, x1\n\t" "add x9, x9, x1\n\t" "add x11, x11, #1\n\t" "subs x8, x8, #1\n\t" "b.ne 1b\n\t"
#define WRAP_B(xb) "cmp " #xb ", x5\n\t" "csel " #xb ", x4, " #xb ", eq\n\t"
#define SEL_OUT "cmp x11, x14\n\t" "csel x20, x9, x10, hs\n\t"
#define ADV_CNT(xc) "add " #xc ", " #xc ", #1\n\t" "cmp " #xc ", x6\n\t" "csel " #xc ", xzr, " #xc ", eq\n\t"
// 行首：L2 预取第 Y+PD 行、把第 Y+1 行（最后一行时拷本行，避免越界）拷到另一槽：ncp_full 个整向量 + 1 个谓词尾向量；x16 = 当前槽
#define ROW_HEAD_COMMON \
        "add x21, x0, x26\n\t" \
        "mov x16, x17\n\t" \
        "sub x17, x28, x17\n\t"                 /* 另一槽 = 2*ring + slot - 当前 */ \
        "add x22, x0, x1\n\t" "cmp x8, #1\n\t" "csel x22, x0, x22, eq\n\t" "mov x23, x17\n\t" \
        "ldr x12, [%[A], #168]\n\t" \
        "cbz x12, 7f\n\t" \
        "3:\n\t" \
        "prfm pldl2keep, [x21]\n\t" \
        "ld1w {z24.s}, p0/z, [x22]\n\t" \
        "st1w {z24.s}, p0, [x23]\n\t" \
        "add x21, x21, #64\n\t" "add x22, x22, #64\n\t" "add x23, x23, #64\n\t" \
        "subs x12, x12, #1\n\t" \
        "b.ne 3b\n\t" \
        "7:\n\t" \
        "prfm pldl2keep, [x21]\n\t" \
        "ld1w {z24.s}, p3/z, [x22]\n\t" \
        "st1w {z24.s}, p3, [x23]\n\t"

// ---------------- 16×1 对：A 用 za0/za1（列 0..15 / 16..31），B 用 za2/za3；槽 512 B ----------------
static void k16pair(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 1, 512, 31 + P->KW);
    asm volatile(
        LOAD_ARGS
        "fmov z31.s, #0.0\n\t"
        "1:\n\t"
        ROW_HEAD_COMMON
        "add x21, x9, x26\n\t"
        "prfm pstl2keep, [x21]\n\t" "prfm pstl2keep, [x21, #64]\n\t"
        "mov x15, x7\n\t"
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
        WRAP_B(x2) WRAP_B(x3) SEL_OUT
        "cmp x27, x24\n\t" "b.hs 4f\n\t"
        "and w12, w27, #15\n\t"
        "mova z8.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za1v.s[w12, 0]\n\t"
        "st1w {z8.s}, p0, [x20]\n\t"
        "st1w {z9.s}, p0, [x20, #1, mul vl]\n\t"
        "mova za0v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p0/m, z31.s\n\t"
        "4:\n\t"
        "cmp x19, x25\n\t" "b.hs 5f\n\t"
        "and w13, w19, #15\n\t"
        "mova z8.s, p0/m, za2v.s[w13, 0]\n\t"
        "mova z9.s, p0/m, za3v.s[w13, 0]\n\t"
        "st1w {z8.s}, p0, [x20]\n\t"
        "st1w {z9.s}, p0, [x20, #1, mul vl]\n\t"
        "mova za2v.s[w13, 0], p0/m, z31.s\n\t"
        "mova za3v.s[w13, 0], p0/m, z31.s\n\t"
        "5:\n\t"
        ADV_CNT(x27) ADV_CNT(x19)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z8", "z9", "z24", "z31", "p0", "p3", "memory", "cc");
}

// ---------------- 16×1 单组：4 tile = 64 列；槽 640 B ----------------
static void k16single(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 1, 640, 63 + P->KW);
    asm volatile(
        LOAD_ARGS
        "fmov z31.s, #0.0\n\t"
        "1:\n\t"
        ROW_HEAD_COMMON
        "add x21, x9, x26\n\t"
        "prfm pstl2keep, [x21]\n\t" "prfm pstl2keep, [x21, #64]\n\t" "prfm pstl2keep, [x21, #128]\n\t" "prfm pstl2keep, [x21, #192]\n\t"
        "mov x15, x7\n\t"
        "2:\n\t"
        "ld1w {z0.s}, p0/z, [x16]\n\t"
        "ld1w {z1.s}, p0/z, [x16, #1, mul vl]\n\t"
        "ld1w {z2.s}, p0/z, [x16, #2, mul vl]\n\t"
        "ld1w {z3.s}, p0/z, [x16, #3, mul vl]\n\t"
        "ld1w {z4.s}, p0/z, [x2]\n\t"
        "fmopa za0.s, p0/m, p0/m, z0.s, z4.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z1.s, z4.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z2.s, z4.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z3.s, z4.s\n\t"
        "add x16, x16, #4\n\t"
        "add x2, x2, #64\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        WRAP_B(x2) SEL_OUT
        "cmp x27, x24\n\t" "b.hs 4f\n\t"
        "and w12, w27, #15\n\t"
        "mova z5.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z6.s, p0/m, za1v.s[w12, 0]\n\t"
        "mova z7.s, p0/m, za2v.s[w12, 0]\n\t"
        "mova z8.s, p0/m, za3v.s[w12, 0]\n\t"
        "st1w {z5.s}, p0, [x20]\n\t"
        "st1w {z6.s}, p0, [x20, #1, mul vl]\n\t"
        "st1w {z7.s}, p0, [x20, #2, mul vl]\n\t"
        "st1w {z8.s}, p0, [x20, #3, mul vl]\n\t"
        "mova za0v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za2v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za3v.s[w12, 0], p0/m, z31.s\n\t"
        "4:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z4", "z5", "z6", "z7", "z8", "z24", "z31", "p0", "p3", "memory", "cc");
}

// ---------------- 8×2：4 tile = 128 列，列 c = 2s+ic；槽 896 B ----------------
static void k8(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 2, 896, 127 + P->KW);
    asm volatile(
        LOAD_ARGS
        "ldr x7, [%[A], #136]\n\t"      // it = steps/2
        "fmov z31.s, #0.0\n\t"
        "1:\n\t"
        ROW_HEAD_COMMON
        // 输出预取：PD 行后是否有事件（(cA+PD) mod KH < nv）
        "ldr x23, [%[A], #144]\n\t"
        "add x22, x27, x23\n\t" "cmp x22, x6\n\t" "sub x21, x22, x6\n\t" "csel x22, x21, x22, hs\n\t"
        "cmp x22, x24\n\t" "b.hs 6f\n\t"
        "add x21, x9, x26\n\t"
        "prfm pstl2keep, [x21]\n\t" "prfm pstl2keep, [x21, #64]\n\t" "prfm pstl2keep, [x21, #128]\n\t" "prfm pstl2keep, [x21, #192]\n\t"
        "prfm pstl2keep, [x21, #256]\n\t" "prfm pstl2keep, [x21, #320]\n\t" "prfm pstl2keep, [x21, #384]\n\t" "prfm pstl2keep, [x21, #448]\n\t"
        "6:\n\t"
        "mov x15, x7\n\t"
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
        WRAP_B(x2) SEL_OUT
        "cmp x27, x24\n\t" "b.hs 4f\n\t"
        "and w12, w27, #7\n\t" "lsl w12, w12, #1\n\t"
        "mova z8.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za0v.s[w12, 1]\n\t"
        "mova z10.s, p0/m, za1v.s[w12, 0]\n\t"
        "mova z11.s, p0/m, za1v.s[w12, 1]\n\t"
        "mova z12.s, p0/m, za2v.s[w12, 0]\n\t"
        "mova z13.s, p0/m, za2v.s[w12, 1]\n\t"
        "mova z14.s, p0/m, za3v.s[w12, 0]\n\t"
        "mova z15.s, p0/m, za3v.s[w12, 1]\n\t"
        "st2w {z8.s, z9.s}, p0, [x20]\n\t"
        "st2w {z10.s, z11.s}, p0, [x20, #2, mul vl]\n\t"
        "st2w {z12.s, z13.s}, p0, [x20, #4, mul vl]\n\t"
        "st2w {z14.s, z15.s}, p0, [x20, #6, mul vl]\n\t"
        "mova za0v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za0v.s[w12, 1], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 1], p0/m, z31.s\n\t"
        "mova za2v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za2v.s[w12, 1], p0/m, z31.s\n\t"
        "mova za3v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za3v.s[w12, 1], p0/m, z31.s\n\t"
        "4:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z4", "z5", "z6", "z7", "z8", "z9", "z10", "z11", "z12", "z13", "z14", "z15", "z24", "z31", "p0", "p3", "memory", "cc");
}

// ---------------- 2×8：4 tile = 512 列，列 c = 8s+ic；a 由 4 ld2w + 两级 uzp 得到 8 步；槽 2560 B ----------------
// 两个 tile 一组交替发 fmopa（同 tile 连续 fmopa 有 4 周期依赖）；b 每步现取（z8）
#define K2_A(XB, OFFV, D0, D1, D2, D3, D4, D5, D6, D7) \
        "ld2w {z0.s, z1.s}, p0/z, [" #XB ", #" #OFFV ", mul vl]\n\t" \
        "ld2w {z2.s, z3.s}, p0/z, [" #XB ", #" #OFFV "+2, mul vl]\n\t" \
        "ld2w {z4.s, z5.s}, p0/z, [" #XB ", #" #OFFV "+4, mul vl]\n\t" \
        "ld2w {z6.s, z7.s}, p0/z, [" #XB ", #" #OFFV "+6, mul vl]\n\t" \
        "uzp1 z8.s, z0.s, z2.s\n\t"   "uzp2 z10.s, z0.s, z2.s\n\t"  "uzp1 z9.s, z1.s, z3.s\n\t"   "uzp2 z11.s, z1.s, z3.s\n\t" \
        "uzp1 z12.s, z4.s, z6.s\n\t"  "uzp2 z14.s, z4.s, z6.s\n\t"  "uzp1 z13.s, z5.s, z7.s\n\t"  "uzp2 z15.s, z5.s, z7.s\n\t" \
        "uzp1 " #D0 ".s, z8.s, z12.s\n\t"  "uzp2 " #D4 ".s, z8.s, z12.s\n\t"  "uzp1 " #D1 ".s, z9.s, z13.s\n\t"  "uzp2 " #D5 ".s, z9.s, z13.s\n\t" \
        "uzp1 " #D2 ".s, z10.s, z14.s\n\t" "uzp2 " #D6 ".s, z10.s, z14.s\n\t" "uzp1 " #D3 ".s, z11.s, z15.s\n\t" "uzp2 " #D7 ".s, z11.s, z15.s\n\t"
#define K2_FM2(TA, TB, q, AA, AB) \
        "ld1w {z8.s}, p0/z, [x2, #" #q ", mul vl]\n\t" \
        "fmopa za" #TA ".s, p0/m, p0/m, " #AA ".s, z8.s\n\t" \
        "fmopa za" #TB ".s, p0/m, p0/m, " #AB ".s, z8.s\n\t"
#define EX8(T, OFF) \
        "mova z0.s, p0/m, za" #T "v.s[w12, 0]\n\t" "mova z1.s, p0/m, za" #T "v.s[w12, 1]\n\t" \
        "mova z2.s, p0/m, za" #T "v.s[w12, 2]\n\t" "mova z3.s, p0/m, za" #T "v.s[w12, 3]\n\t" \
        "mova z4.s, p0/m, za" #T "v.s[w13, 0]\n\t" "mova z5.s, p0/m, za" #T "v.s[w13, 1]\n\t" \
        "mova z6.s, p0/m, za" #T "v.s[w13, 2]\n\t" "mova z7.s, p0/m, za" #T "v.s[w13, 3]\n\t" \
        "zip1 z16.s, z0.s, z4.s\n\t" "zip1 z17.s, z1.s, z5.s\n\t" "zip1 z18.s, z2.s, z6.s\n\t" "zip1 z19.s, z3.s, z7.s\n\t" \
        "zip2 z20.s, z0.s, z4.s\n\t" "zip2 z21.s, z1.s, z5.s\n\t" "zip2 z22.s, z2.s, z6.s\n\t" "zip2 z23.s, z3.s, z7.s\n\t" \
        "st4w {z16.s, z17.s, z18.s, z19.s}, p0, [x20, #" #OFF ", mul vl]\n\t" \
        "st4w {z20.s, z21.s, z22.s, z23.s}, p0, [x20, #" #OFF "+4, mul vl]\n\t" \
        "mova za" #T "v.s[w12, 0], p0/m, z8.s\n\t" "mova za" #T "v.s[w12, 1], p0/m, z8.s\n\t" \
        "mova za" #T "v.s[w12, 2], p0/m, z8.s\n\t" "mova za" #T "v.s[w12, 3], p0/m, z8.s\n\t" \
        "mova za" #T "v.s[w13, 0], p0/m, z8.s\n\t" "mova za" #T "v.s[w13, 1], p0/m, z8.s\n\t" \
        "mova za" #T "v.s[w13, 2], p0/m, z8.s\n\t" "mova za" #T "v.s[w13, 3], p0/m, z8.s\n\t"
static void k2(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 8, 2560, 504 + P->steps);
    asm volatile(
        LOAD_ARGS
        "ldr x7, [%[A], #136]\n\t"      // it = steps/8
        "1:\n\t"
        ROW_HEAD_COMMON
        "mov x15, x7\n\t"
        "2:\n\t"
        "add x23, x16, #1024\n\t"
        K2_A(x16, 0, z16, z17, z18, z19, z20, z21, z22, z23)
        K2_A(x16, 8, z24, z25, z26, z27, z28, z29, z30, z31)
        K2_FM2(0, 1, 0, z16, z24) K2_FM2(0, 1, 1, z17, z25) K2_FM2(0, 1, 2, z18, z26) K2_FM2(0, 1, 3, z19, z27)
        K2_FM2(0, 1, 4, z20, z28) K2_FM2(0, 1, 5, z21, z29) K2_FM2(0, 1, 6, z22, z30) K2_FM2(0, 1, 7, z23, z31)
        K2_A(x23, 0, z16, z17, z18, z19, z20, z21, z22, z23)
        K2_A(x23, 8, z24, z25, z26, z27, z28, z29, z30, z31)
        K2_FM2(2, 3, 0, z16, z24) K2_FM2(2, 3, 1, z17, z25) K2_FM2(2, 3, 2, z18, z26) K2_FM2(2, 3, 3, z19, z27)
        K2_FM2(2, 3, 4, z20, z28) K2_FM2(2, 3, 5, z21, z29) K2_FM2(2, 3, 6, z22, z30) K2_FM2(2, 3, 7, z23, z31)
        "add x16, x16, #32\n\t"
        "add x2, x2, #512\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        WRAP_B(x2) SEL_OUT
        "cmp x27, x24\n\t" "b.hs 4f\n\t"
        "and w12, w27, #1\n\t" "lsl w12, w12, #3\n\t" "add w13, w12, #4\n\t"
        "fmov z8.s, #0.0\n\t"
        EX8(0, 0)
        EX8(1, 8)
        EX8(2, 16)
        EX8(3, 24)
        "4:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, VCLOB, "p0", "p3", "memory", "cc");
}


// ---------------- 1×16：1 个残差 × 16 个 X 偏移；2 计算 tile（za0/za1，各 256 列）+ 2 转置 tile（za2/za3）----------------
// a(X)[r] = row[base_t + 16r + X]（stride 16）：把 16 行 row[base_t + 16q + X0 .. +15]（q=0..15）横向装进 za(2+t)，
// 竖切片 c 就是 a(X0+c)。每 16 步：32 条 ld1w→ZA + 32 条 mova + 16 条 b 载入 + 32 条 fmopa。链结束时整 tile 就是
// 输出行的 256 个连续 float：16 条 st1w za?h 直接落盘，再 zero。步数 = KW+15（最后一块不满 16 步）。槽 2560 B。
#define K1_LD(ZT, W, I, XB) "ld1w {za" #ZT "h.s[" #W ", " #I "]}, p0/z, [" #XB ", x21, lsl #2]\n\t" "add x21, x21, #16\n\t"
#define K1_SAVE(ZT, W, I, XB) "st1w {za" #ZT "h.s[" #W ", " #I "]}, p0, [" #XB ", x21, lsl #2]\n\t" "add x21, x21, #16\n\t"
#define K1_TR(ZT, XB) \
        "mov x21, #0\n\t" "mov w12, #0\n\t" \
        K1_LD(ZT, w12, 0, XB) K1_LD(ZT, w12, 1, XB) K1_LD(ZT, w12, 2, XB) K1_LD(ZT, w12, 3, XB) \
        "mov w12, #4\n\t" \
        K1_LD(ZT, w12, 0, XB) K1_LD(ZT, w12, 1, XB) K1_LD(ZT, w12, 2, XB) K1_LD(ZT, w12, 3, XB) \
        "mov w12, #8\n\t" \
        K1_LD(ZT, w12, 0, XB) K1_LD(ZT, w12, 1, XB) K1_LD(ZT, w12, 2, XB) K1_LD(ZT, w12, 3, XB) \
        "mov w12, #12\n\t" \
        K1_LD(ZT, w12, 0, XB) K1_LD(ZT, w12, 1, XB) K1_LD(ZT, w12, 2, XB) K1_LD(ZT, w12, 3, XB)
#define K1_ST(ZT, XB) \
        "mov x21, #0\n\t" "mov w12, #0\n\t" \
        K1_SAVE(ZT, w12, 0, XB) K1_SAVE(ZT, w12, 1, XB) K1_SAVE(ZT, w12, 2, XB) K1_SAVE(ZT, w12, 3, XB) \
        "mov w12, #4\n\t" \
        K1_SAVE(ZT, w12, 0, XB) K1_SAVE(ZT, w12, 1, XB) K1_SAVE(ZT, w12, 2, XB) K1_SAVE(ZT, w12, 3, XB) \
        "mov w12, #8\n\t" \
        K1_SAVE(ZT, w12, 0, XB) K1_SAVE(ZT, w12, 1, XB) K1_SAVE(ZT, w12, 2, XB) K1_SAVE(ZT, w12, 3, XB) \
        "mov w12, #12\n\t" \
        K1_SAVE(ZT, w12, 0, XB) K1_SAVE(ZT, w12, 1, XB) K1_SAVE(ZT, w12, 2, XB) K1_SAVE(ZT, w12, 3, XB)
static void k1(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 16, 2560, 496 + P->steps);
    A.it = P->steps / 16;                     // 满块数
    A.nvB = P->steps % 16;                    // 尾块步数（借 nvB 字段）
    asm volatile(
        LOAD_ARGS
        "ldr x7, [%[A], #136]\n\t"      // 满块数
        "1:\n\t"
        ROW_HEAD_COMMON
        "mov x15, x7\n\t"
        "mov x22, x16\n\t"              // 本块 X0 处的 a 基址
        "cbz x15, 8f\n\t"
        "2:\n\t"
        K1_TR(2, x22)
        "add x23, x22, #1024\n\t"
        K1_TR(3, x23)
        "mov w13, #0\n\t"
        "mov x21, #16\n\t"
        "3:\n\t"
        "mova z0.s, p0/m, za2v.s[w13, 0]\n\t"
        "mova z1.s, p0/m, za3v.s[w13, 0]\n\t"
        "ld1w {z2.s}, p0/z, [x2]\n\t"
        "fmopa za0.s, p0/m, p0/m, z0.s, z2.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z1.s, z2.s\n\t"
        "add w13, w13, #1\n\t"
        "add x2, x2, #64\n\t"
        "subs x21, x21, #1\n\t"
        "b.ne 3b\n\t"
        "add x22, x22, #64\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        "8:\n\t"
        "cbz x25, 9f\n\t"               // 尾块
        K1_TR(2, x22)
        "add x23, x22, #1024\n\t"
        K1_TR(3, x23)
        "mov w13, #0\n\t"
        "mov x21, x25\n\t"
        "3:\n\t"
        "mova z0.s, p0/m, za2v.s[w13, 0]\n\t"
        "mova z1.s, p0/m, za3v.s[w13, 0]\n\t"
        "ld1w {z2.s}, p0/z, [x2]\n\t"
        "fmopa za0.s, p0/m, p0/m, z0.s, z2.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z1.s, z2.s\n\t"
        "add w13, w13, #1\n\t"
        "add x2, x2, #64\n\t"
        "subs x21, x21, #1\n\t"
        "b.ne 3b\n\t"
        "9:\n\t"
        WRAP_B(x2) SEL_OUT
        "cmp x27, x24\n\t" "b.hs 4f\n\t"
        K1_ST(0, x20)
        "add x22, x20, #1024\n\t"
        K1_ST(1, x22)
        "zero {za0.s, za1.s}\n\t"
        "4:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z24", "p0", "p3", "memory", "cc");
}

// ---------------- b 表 ----------------
// kind 16: R[y][X][c] = k[(y-c) mod KH][X]（残差 s_base+c 无效 → 0）
// kind 8 : c = 2s+ic: k[(y-s) mod KH][X-ic]
// kind 2 : c = 8s+ic: k[(y-s) mod KH][X-ic]
static void build_R(float* R, const float* k, long KH, long KW, long steps, long s_base, int kind)
{
    for (long y = 0; y < KH; y++)
        for (long X = 0; X < steps; X++)
            for (long c = 0; c < 16; c++) {
                long s, ic;
                if (kind == 16) { s = c; ic = 0; } else if (kind == 8) { s = c >> 1; ic = c & 1; } else if (kind == 2) { s = c >> 3; ic = c & 7; } else { s = 0; ic = c; }
                long ki = X - ic, kj = ((y - s) % KH + KH) % KH;
                R[(y * steps + X) * 16 + c] = (ki >= 0 && ki < KW && s_base + s < KH) ? k[kj * KW + ki] : 0.f;
            }
}

// ---------------- 计划：残差分组 → 工作项 ----------------
typedef struct { int kind; long s_base, nvA, nvB, width, steps; float* R; long RSB; } grp_t;   // kind: 32=pair,16=single,8,2
typedef struct { int g; long base; } item_t;

static int plan(long KH, long KW, grp_t* G, const float* k)
{
    int ng = 0; long s = 0;
    long n16 = KH / 16, rem = KH - n16 * 16;
    // 16 组：成对
    while (n16 >= 2) { G[ng++] = (grp_t){32, s, 16, 16, 32, KW, NULL, 0}; s += 32; n16 -= 2; }
    if (n16 == 1) { G[ng++] = (grp_t){16, s, 16, 0, 64, KW, NULL, 0}; s += 16; }
    if (rem >= 3) { long nv = rem > 8 ? 8 : rem; G[ng++] = (grp_t){8, s, nv, 0, 128, (KW + 1 + 1) & ~1L, NULL, 0}; s += nv; rem -= nv; }
    int useK2 = getenv("USEK2") != NULL;
    while (rem > 0) {
        if (useK2) { long nv = rem > 2 ? 2 : rem; G[ng++] = (grp_t){2, s, nv, 0, 512, (KW + 7 + 7) & ~7L, NULL, 0}; s += nv; rem -= nv; }
        else { G[ng++] = (grp_t){1, s, 1, 0, 512, KW + 15, NULL, 0}; s += 1; rem -= 1; }
    }
    for (int g = 0; g < ng; g++) {
        G[g].RSB = G[g].steps * 64;
        G[g].R = alloc_big((size_t)KH * G[g].RSB);
        int kind = G[g].kind == 32 ? 16 : G[g].kind;
        build_R(G[g].R, k, KH, KW, G[g].steps, G[g].s_base, kind);
    }
    return ng;
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
    int nthr = argc > 5 ? atoi(argv[5]) : 38;
    int check = argc > 6 ? atoi(argv[6]) : 1;
    if (getenv("PD")) PD = atol(getenv("PD"));
    long outH = H - KH + 1, outW = W - KW + 1;
    setvbuf(stdout, NULL, _IONBF, 0);
    float* in = alloc_big((size_t)H * W * 4);
    float* out = alloc_big((size_t)H * W * 4);
    float* k = malloc(KH * KW * 4);
    srand(1);
    for (long i = 0; i < H * W; i++) in[i] = (float)rand() / RAND_MAX;
    for (long i = 0; i < KH * KW; i++) k[i] = (float)rand() / RAND_MAX;
    const double ghz = 1.55;
    grp_t G[16]; int ng = plan(KH, KW, G, k);
    printf("H=%ld W=%ld KH=%ld KW=%ld threads=%d PD=%ld  groups:", H, W, KH, KW, nthr, PD);
    double tile_steps = 0;
    for (int g = 0; g < ng; g++) {
        long nstrip = (outW + G[g].width - 1) / G[g].width;
        printf(" [%s s=%ld nv=%ld/%ld w=%ld steps=%ld strips=%ld]", G[g].kind == 32 ? "pair" : G[g].kind == 16 ? "single" : G[g].kind == 8 ? "8x2" : G[g].kind == 2 ? "2x8" : "1x16",
               G[g].s_base, G[g].nvA, G[g].nvB, G[g].width, G[g].steps, nstrip);
        tile_steps += (G[g].kind == 1 ? 2.0 : 4.0) * G[g].steps * nstrip;
    }
    double useful = (double)outW * KH * KW / 256.0;
    printf("\n  X/量化效率 %.1f%%（tile-步 %.0f vs 有用 %.0f，每输入行）\n", 100 * useful / tile_steps, tile_steps, useful);

    // 工作项：每组的条带（最后一条带右对齐到 outW-width）
    item_t items[4096]; int nit = 0; double* cost = malloc(4096 * sizeof(double)); double C = 0;
    int only = getenv("ONLY") ? atoi(getenv("ONLY")) : 0;          // 只跑某种 kind（32/16/8/2）的项
    int dyn = getenv("DYN") ? atoi(getenv("DYN")) : 0;             // 动态认领；值 = 每项竖切块数
    double wK8 = getenv("W8") ? atof(getenv("W8")) : 1.0, wK2 = getenv("W2") ? atof(getenv("W2")) : 1.0;   // 静态划分的相对代价权重
    for (int g = 0; g < ng; g++) {
        if (only && G[g].kind != only) continue;
        long nstrip = (outW + G[g].width - 1) / G[g].width;
        for (long s = 0; s < nstrip; s++) {
            long base = s * G[g].width; if (base + G[g].width > outW) base = outW - G[g].width;
            items[nit] = (item_t){g, base}; cost[nit] = (double)G[g].steps * outH * (G[g].kind == 8 ? wK8 : G[g].kind == 2 ? wK2 : G[g].kind == 1 ? 0.5 * wK2 : 1.0); C += cost[nit]; nit++;
        }
    }
    printf("  items=%d  每线程 %.2f 项  only=%d dyn=%d\n", nit, (double)nit / nthr, only, dyn);
    double tsteps_total = 0; for (int i = 0; i < nit; i++) tsteps_total += 4.0 * G[items[i].g].steps * (outH + KH - 1);
    volatile long g_next __attribute__((aligned(64))) = 0;
    long* thr_ts = calloc(nthr, sizeof(long));
    float* scratch = alloc_big((size_t)nthr * 8192);
    float* rings = alloc_big((size_t)nthr * 8192);       // 每线程 8 KB 环（2 槽，eor 换槽要求 ring 对齐到 2*slot 且 slot 为 2 的幂倍... 这里用 8 KB 对齐 + slot 大小的 eor）

    double best = 1e9; double* thr_ms = calloc(nthr, sizeof(double));
    for (int rep = 0; rep < 3; rep++) {
        for (long i = 0; i < H * W; i++) out[i] = NAN;
        double t0 = now();
        #pragma omp parallel num_threads(nthr)
        {
            int t = omp_get_thread_num();
            double c_lo = C * t / nthr, c_hi = C * (t + 1) / nthr, acc = 0;
            uint64_t k0 = cyc(); long ts = 0;
            SMSTART();
            for (int ii = 0; ii < (dyn ? nit * dyn : nit); ii++) {
                int i; long ja, jb;
                if (dyn) {
                    long w = __atomic_fetch_add(&g_next, 1, __ATOMIC_RELAXED); if (w >= (long)nit * dyn) break;
                    i = (int)(w / dyn); long ch = w % dyn; ja = outH * ch / dyn; jb = outH * (ch + 1) / dyn;
                } else {
                    i = ii;
                    double a0 = acc, a1 = acc + cost[i]; acc = a1;
                    if (a1 <= c_lo || a0 >= c_hi) continue;
                    double f0 = (c_lo > a0 ? (c_lo - a0) / cost[i] : 0), f1 = (c_hi < a1 ? (c_hi - a0) / cost[i] : 1);
                    ja = (long)(f0 * outH + 0.5); jb = (long)(f1 * outH + 0.5);
                }
                if (jb <= ja) continue;
                const grp_t* g = &G[items[i].g];
                ts += (g->kind == 1 ? 2L : 4L) * g->steps * (jb - ja + KH - 1);
                kp_t P = { in + ja * W + items[i].base, W * 4, g->R, g->RSB, KH, g->steps, jb - ja + KH - 1,
                           out + (ja - KH + 1) * W + items[i].base, scratch + t * 2048,
                           ((ja + 1 - g->s_base) % KH + KH) % KH, ((ja + 1 - g->s_base - 16) % KH + KH) % KH,
                           ((ja - g->s_base) % KH + KH) % KH, ((ja - g->s_base - 16) % KH + KH) % KH, g->nvA, g->nvB, rings + t * 2048, KW };
                asm volatile("zero {za}" ::: "memory");
                if (g->kind == 32) k16pair(&P); else if (g->kind == 16) k16single(&P); else if (g->kind == 8) k8(&P); else if (g->kind == 2) k2(&P); else k1(&P);
            }
            SMSTOP();
            thr_ms[t] = (double)(cyc() - k0) / cfrq() * 1e3; thr_ts[t] = ts;
        }
        g_next = 0;
        double t = now() - t0;
        if (t < best) best = t;
        double mn = 1e9, mx = 0, av = 0;
        for (int i = 0; i < nthr; i++) { if (thr_ms[i] < mn) mn = thr_ms[i]; if (thr_ms[i] > mx) mx = thr_ms[i]; av += thr_ms[i] / nthr; }
        double cps_mn = 1e9, cps_mx = 0;
        for (int i = 0; i < nthr; i++) if (thr_ts[i]) { double c = thr_ms[i] * 1e-3 * ghz * 1e9 / thr_ts[i]; if (c < cps_mn) cps_mn = c; if (c > cps_mx) cps_mx = c; }
        printf("  rep %d: %.3f ms  %.0f GFLOPS  线程 min/avg/max %.3f/%.3f/%.3f ms  周期/tile步 %.2f–%.2f (理想 2, 按 1.55 GHz)\n", rep, t * 1e3, 2.0 * outH * outW * KH * KW / t * 1e-9, mn, av, mx, cps_mn, cps_mx);
        if (getenv("THR") && rep == 2) { printf("   "); for (int i = 0; i < nthr; i++) if (thr_ts[i]) printf(" %d:%.2f", i, thr_ms[i] * 1e-3 * ghz * 1e9 / thr_ts[i]); printf("\n"); }
    }
    double flops = 2.0 * outH * outW * KH * KW;
    printf("  best %.3f ms = %.0f GFLOPS（峰值 %.0f，占 %.1f%%）\n", best * 1e3, flops / best * 1e-9, 38 * 128 * 2 * ghz, flops / best * 1e-9 / (38 * 128 * 2 * ghz) * 100);

    if (check) {
        long bad = 0, nan_cnt = 0;
        #pragma omp parallel for reduction(+:bad,nan_cnt) schedule(dynamic, 8)
        for (long j = 0; j < outH; j++)
            for (long i = 0; i < outW; i++) {
                float o = out[j * W + i];
                if (isnan(o)) { nan_cnt++; continue; }
                float r = ref_out(in, W, k, KH, KW, j, i);
                if (memcmp(&r, &o, 4) != 0) bad++;
            }
        printf("  correctness: %ld 未写(NaN), %ld 不一致 → %s\n", nan_cnt, bad, (bad || nan_cnt) ? "FAIL" : "PASS(bit-exact)");
    }
    return 0;
}
