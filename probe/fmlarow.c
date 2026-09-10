// 第 5 行 FMLA 方案可行性探针：
//  (A) 每步 4 条非对齐 a + 1 条对齐 b(64B) + 1 条 ld1rqw + 4 fmopa + 8 fmla（索引）+ 每 4 步 20 条“触碰”载入，数据固定（L1）
//  (B) 同 (A)，但平面槽在 100 KB 环上轮转（L2），触碰载入提前一行把下一槽的行拉进 L1
// gcc -O2 -march=armv9-a+sme+sve2 fmlarow.c -o fmlarow
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + ts.tv_nsec * 1e-9; }
#define VCLOB "z0","z1","z2","z3","z4","z5","z6","z7","z8","z9","z10","z11","z12","z13","z14","z15","z16","z17","z18","z19","z20","z21","z22","z23","z24","z25","z26","z27","z28","z29","z30","z31","p0"

#define OPA(t, a, b) "fmopa za" #t ".s, p0/m, p0/m, z" #a ".s, z" #b ".s\n\t"
// 一步：a0..a3 非对齐（p + 16t 元素 + 移位 s 字节），b 对齐，kq 16B
#define STEP(pq, B, K, A0, A1, A2, A3, FM)                                                     \
    "ld1w {z" #B ".s}, p0/z, [%[pb]]\n\t"                                                       \
    "ld1rqw {z" #K ".s}, p0/z, [%[pk]]\n\t"                                                     \
    "ld1w {z" #A0 ".s}, p0/z, [%[" #pq "]]\n\t"                                                 \
    "ld1w {z" #A1 ".s}, p0/z, [%[" #pq "], #1, mul vl]\n\t"                                     \
    "ld1w {z" #A2 ".s}, p0/z, [%[" #pq "], #2, mul vl]\n\t"                                     \
    "ld1w {z" #A3 ".s}, p0/z, [%[" #pq "], #3, mul vl]\n\t"                                     \
    "add %[pb], %[pb], #64\n\t add %[pk], %[pk], #16\n\t"                                       \
    OPA(0, A0, B) FM(A0, K, 24, 25) OPA(1, A1, B) FM(A0, K, 26, 27)                              \
    OPA(2, A2, B) FM(A1, K, 28, 29) OPA(3, A3, B) FM(A1, K, 30, 31)
#define FM8(a, k, r0, r1) "fmla z" #r0 ".s, z" #a ".s, z" #k ".s[0]\n\t fmla z" #r1 ".s, z" #a ".s, z" #k ".s[1]\n\t"
#define FM0(a, k, r0, r1)
#define TOUCH5(pt) "ld1w {z23.s}, p0/z, [%[" #pt "]]\n\t ld1w {z23.s}, p0/z, [%[" #pt "], #1, mul vl]\n\t" \
    "ld1w {z23.s}, p0/z, [%[" #pt "], #2, mul vl]\n\t ld1w {z23.s}, p0/z, [%[" #pt "], #3, mul vl]\n\t ld1w {z23.s}, p0/z, [%[" #pt "], #4, mul vl]\n\t add %[" #pt "], %[" #pt "], #320\n\t"

// 一行：m4 个 4 步组（每组 4 个平面各一步 + 触碰 20 线：下一槽的 4 个平面各 5 线）
#define FM4(a, k, r0, r1) "fmla z" #r0 ".s, z" #a ".s, z" #k ".s[0]\n\t"
#define STEPB(pq, B, K, A0, A1, A2, A3, FM, BADV)                                              \
    "ld1w {z" #B ".s}, p0/z, [%[pb]]\n\t"                                                       \
    "ld1rqw {z" #K ".s}, p0/z, [%[pk]]\n\t"                                                     \
    "ld1w {z" #A0 ".s}, p0/z, [%[" #pq "]]\n\t"                                                 \
    "ld1w {z" #A1 ".s}, p0/z, [%[" #pq "], #1, mul vl]\n\t"                                     \
    "ld1w {z" #A2 ".s}, p0/z, [%[" #pq "], #2, mul vl]\n\t"                                     \
    "ld1w {z" #A3 ".s}, p0/z, [%[" #pq "], #3, mul vl]\n\t"                                     \
    "add %[pb], %[pb], #" #BADV "\n\t add %[pk], %[pk], #16\n\t"                                \
    OPA(0, A0, B) FM(A0, K, 24, 25) OPA(1, A1, B) FM(A0, K, 26, 27)                              \
    OPA(2, A2, B) FM(A1, K, 28, 29) OPA(3, A3, B) FM(A1, K, 30, 31)
static void run_row(const float* p0, const float* p1, const float* p2, const float* p3, const float* pb, const float* pk,
                    const float* pt, long m4, int fm, int touch, int badv)
{
    long m = m4;
    if (fm == 2)
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEPB(p0, 4, 5, 8, 9, 10, 11, FM4, 64) STEPB(p1, 6, 7, 12, 13, 14, 15, FM4, 64)
                     STEPB(p2, 4, 5, 16, 17, 18, 19, FM4, 64) STEPB(p3, 6, 7, 20, 21, 22, 23, FM4, 64)
                     "add %[p0], %[p0], #4\n\t add %[p1], %[p1], #4\n\t add %[p2], %[p2], #4\n\t add %[p3], %[p3], #4\n\t"
                     "subs %[m], %[m], #1\n\t b.ne 1b\n\t"
                     : [p0] "+r"(p0), [p1] "+r"(p1), [p2] "+r"(p2), [p3] "+r"(p3), [pb] "+r"(pb), [pk] "+r"(pk), [m] "+r"(m)
                     : : "memory", "cc", VCLOB);
    else if (badv == 16)
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEPB(p0, 4, 5, 8, 9, 10, 11, FM0, 16) STEPB(p1, 6, 7, 12, 13, 14, 15, FM0, 16)
                     STEPB(p2, 4, 5, 16, 17, 18, 19, FM0, 16) STEPB(p3, 6, 7, 20, 21, 22, 23, FM0, 16)
                     "add %[p0], %[p0], #4\n\t add %[p1], %[p1], #4\n\t add %[p2], %[p2], #4\n\t add %[p3], %[p3], #4\n\t"
                     "subs %[m], %[m], #1\n\t b.ne 1b\n\t"
                     : [p0] "+r"(p0), [p1] "+r"(p1), [p2] "+r"(p2), [p3] "+r"(p3), [pb] "+r"(pb), [pk] "+r"(pk), [m] "+r"(m)
                     : : "memory", "cc", VCLOB);
    else if (fm && touch)
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP(p0, 4, 5, 8, 9, 10, 11, FM8) TOUCH5(pt) STEP(p1, 6, 7, 12, 13, 14, 15, FM8) TOUCH5(pt)
                     STEP(p2, 4, 5, 16, 17, 18, 19, FM8) TOUCH5(pt) STEP(p3, 6, 7, 20, 21, 22, 23, FM8) TOUCH5(pt)
                     "add %[p0], %[p0], #4\n\t add %[p1], %[p1], #4\n\t add %[p2], %[p2], #4\n\t add %[p3], %[p3], #4\n\t"
                     "subs %[m], %[m], #1\n\t b.ne 1b\n\t"
                     : [p0] "+r"(p0), [p1] "+r"(p1), [p2] "+r"(p2), [p3] "+r"(p3), [pb] "+r"(pb), [pk] "+r"(pk), [pt] "+r"(pt), [m] "+r"(m)
                     : : "memory", "cc", VCLOB);
    else if (fm)
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP(p0, 4, 5, 8, 9, 10, 11, FM8) STEP(p1, 6, 7, 12, 13, 14, 15, FM8)
                     STEP(p2, 4, 5, 16, 17, 18, 19, FM8) STEP(p3, 6, 7, 20, 21, 22, 23, FM8)
                     "add %[p0], %[p0], #4\n\t add %[p1], %[p1], #4\n\t add %[p2], %[p2], #4\n\t add %[p3], %[p3], #4\n\t"
                     "subs %[m], %[m], #1\n\t b.ne 1b\n\t"
                     : [p0] "+r"(p0), [p1] "+r"(p1), [p2] "+r"(p2), [p3] "+r"(p3), [pb] "+r"(pb), [pk] "+r"(pk), [m] "+r"(m)
                     : : "memory", "cc", VCLOB);
    else if (touch)
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP(p0, 4, 5, 8, 9, 10, 11, FM0) TOUCH5(pt) STEP(p1, 6, 7, 12, 13, 14, 15, FM0) TOUCH5(pt)
                     STEP(p2, 4, 5, 16, 17, 18, 19, FM0) TOUCH5(pt) STEP(p3, 6, 7, 20, 21, 22, 23, FM0) TOUCH5(pt)
                     "add %[p0], %[p0], #4\n\t add %[p1], %[p1], #4\n\t add %[p2], %[p2], #4\n\t add %[p3], %[p3], #4\n\t"
                     "subs %[m], %[m], #1\n\t b.ne 1b\n\t"
                     : [p0] "+r"(p0), [p1] "+r"(p1), [p2] "+r"(p2), [p3] "+r"(p3), [pb] "+r"(pb), [pk] "+r"(pk), [pt] "+r"(pt), [m] "+r"(m)
                     : : "memory", "cc", VCLOB);
    else
        asm volatile("ptrue p0.s\n\t 1:\n\t"
                     STEP(p0, 4, 5, 8, 9, 10, 11, FM0) STEP(p1, 6, 7, 12, 13, 14, 15, FM0)
                     STEP(p2, 4, 5, 16, 17, 18, 19, FM0) STEP(p3, 6, 7, 20, 21, 22, 23, FM0)
                     "add %[p0], %[p0], #4\n\t add %[p1], %[p1], #4\n\t add %[p2], %[p2], #4\n\t add %[p3], %[p3], #4\n\t"
                     "subs %[m], %[m], #1\n\t b.ne 1b\n\t"
                     : [p0] "+r"(p0), [p1] "+r"(p1), [p2] "+r"(p2), [p3] "+r"(p3), [pb] "+r"(pb), [pk] "+r"(pk), [m] "+r"(m)
                     : : "memory", "cc", VCLOB);
}

int main(int argc, char** argv)
{
    long iters = argc > 1 ? atol(argv[1]) : 100000;
    setvbuf(stdout, NULL, _IONBF, 0);
    const long PW = 96, SB = 2048, NS = 46, m4 = 10;          // k39 形态：每行 40 步
    char* ring = aligned_alloc(4096, (size_t)NS * SB + 4096); memset(ring, 0, (size_t)NS * SB + 4096);
    float* R2 = aligned_alloc(4096, 64 * 64 + 4096); memset(R2, 0, 64 * 64 + 4096);   // 对齐 b：每步 64 B
    float* KP = aligned_alloc(4096, 4096); memset(KP, 0, 4096);
    const char* names[] = {"仅 fmopa（非对齐 a，固定槽 L1）", "fmopa+8fmla（固定槽）", "fmopa+触碰（固定槽）", "fmopa+8fmla+触碰（固定槽）",
                           "仅 fmopa（槽轮转 L2，无触碰）", "fmopa+8fmla（槽轮转，无触碰）", "fmopa+触碰（槽轮转，触碰下一槽）", "fmopa+8fmla+触碰（槽轮转）",
                           "仅 fmopa（槽轮转 + R2 行推进 64B 对齐 b）", "仅 fmopa（槽轮转 + R 行推进 16B b）", "fmopa+4fmla（槽轮转 + R2 推进）"};
    float* Rbig = aligned_alloc(4096, 256 * 1024 + 8192); memset(Rbig, 0, 256 * 1024 + 8192);   // 128 KB 的 b 流区域
    for (int mode = 0; mode < 11; mode++) {
        int rot = mode >= 4, fm = (mode < 8) ? (mode & 1) : (mode == 10 ? 2 : 0), touch = (mode < 8) ? ((mode >> 1) & 1) : 0;
        int badv = mode == 8 || mode == 10 ? 64 : mode == 9 ? 16 : 0;
        double t = 0;
        asm volatile("smstart\n\t" ::: "memory", VCLOB);
        asm volatile("zero {za}\n\t" ::: "memory");
        for (int w = 0; w < 2; w++) {
            long n = w ? iters : iters / 10;
            double t0 = now();
            for (long i = 0; i < n; i++) {
                long slot = rot ? (i % NS) : 0, slot_n = rot ? ((i + 1) % NS) : 0;
                const float* base = (const float*)(ring + slot * SB) + 1;    // +4 B：非对齐
                const float* tb = (const float*)(ring + slot_n * SB);
                const float* pbx = badv ? (const float*)((const char*)Rbig + ((i * 40 * badv) % (128 * 1024))) : R2;
                run_row(base, base + PW, base + 2 * PW, base + 3 * PW, pbx, KP, tb, m4, fm, touch, badv ? badv : 64);
            }
            t = now() - t0;
        }
        asm volatile("smstop\n\t" ::: "memory", VCLOB);
        volatile double cyc = t / iters * 1.55e9 / (m4 * 4);
        printf("  %-44s %6.2f 周期/步 (理想 8)\n", names[mode], cyc);
    }
    return 0;
}
