// 地址别名扫描：固定 L1 数据下，平面基址偏移 / R 行距对 row_steps 每步周期的影响
// gcc -O3 -march=armv9-a+sme+sve2 -fopenmp alias.c -o alias -lm
#include "../conv2d.c"
#include <time.h>

static double now2(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + ts.tv_nsec * 1e-9; }

static char* Pbuf; static char* Rbuf;

// poff: 平面基址相对 4 KB 边界的偏移；rsb: R 行距（字节）；rgap: 两条 b 流的行距倍数（默认 4 行）
static double trial(int KW, long poff, long rsb, long PWb, int var, int nt, long iters)
{
    const long m4 = (KW + 3) / 4, rem = (KW + 3) % 4;
    const long m1 = 4 < m4 ? 4 : m4, m2 = m4 - m1;
    const float* P = (const float*)(Pbuf + poff);
    const float* pb0 = (const float*)(Rbuf + 4 * rsb);
    const float* pb1 = (const float*)(Rbuf);
    long PW = PWb / 4;
    double res = 0;
    sme_start(); sme_zero_za();
    for (int w = 0; w < 2; w++) {
        long it = w == 0 ? iters / 10 : iters;
        double t0 = now2();
        for (long i = 0; i < it; i++)
            row_steps(var, nt, P, P + PW, P + 2 * PW, P + 3 * PW, pb0, pb1, m1, m2, rem, 0);
        double t = now2() - t0;
        if (w == 1) res = t / it * 1.55e9 / (KW + 3);
    }
    sme_stop();
    return res;
}

int main(int argc, char** argv)
{
    long iters = argc > 1 ? atol(argv[1]) : 40000;
    setvbuf(stdout, NULL, _IONBF, 0);
    Pbuf = alloc_aligned(1 << 20); Rbuf = alloc_aligned(1 << 20);
    memset(Pbuf, 0, 1 << 20); memset(Rbuf, 0, 1 << 20);
    int kws[] = {39, 55, 81};
    for (int ki = 0; ki < 3; ki++) {
        int KW = kws[ki];
        long rsb = 16L * (KW + 6);
        long PWb = ((KW + 2) / 4 + 65 + 15) / 16 * 16 * 4;
        printf("KW=%d  RS=%ld B（4 行=%ld, mod4K=%ld） PW=%ld B\n", KW, rsb, 4 * rsb, (4 * rsb) % 4096, PWb);
        printf("  平面基址偏移扫描（R 固定）:");
        for (long poff = 0; poff < 4096; poff += 128) {
            double c = trial(KW, poff, rsb, PWb, 3, 2, iters);
            printf(" %ld:%.1f", poff, c);
        }
        printf("\n  R 行距填充扫描（平面偏移 0）:");
        for (long pad = 0; pad <= 1024; pad += 64) {
            double c = trial(KW, 0, rsb + pad, PWb, 3, 2, iters);
            printf(" +%ld:%.1f", pad, c);
        }
        printf("\n  平面行距扫描（R 固定, 平面偏移 0）:");
        for (long pad = 0; pad <= 512; pad += 64) {
            double c = trial(KW, 0, rsb, PWb + pad, 3, 2, iters);
            printf(" +%ld:%.1f", pad, c);
        }
        printf("\n");
    }
    return 0;
}
