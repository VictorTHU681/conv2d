// 直接测 conv2d.c 内核 row_steps 的每步周期：固定 L1 数据 / 环形槽轮转（L2）/ R 行推进
// gcc -O3 -march=armv9-a+sme+sve2 -fopenmp rowbench.c -o rowbench -lm
#include "../conv2d.c"
#include <time.h>


static double now2(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + ts.tv_nsec * 1e-9; }

// rotate_slots: 0 固定槽；1 全部 NS 槽轮转；>1 在该数量的槽内轮转。var==0 表示只做载入（无 fmopa）
static void trial(const char* tag, int KW, int KH, int rotate_slots, int rotate_R, int var, int nt, long iters)
{
    const long NY = KH + 3, NS = KH + 3, RS = pow2_stride(16L * (KW + 6)) / 4;
    const long m4 = (KW + 3) / 4, rem = (KW + 3) % 4;
    long PW = 16 * ((m4 - 1) / 16) + 80; if (PW < m4 + 64) PW = m4 + 64; PW = (PW + 15) & ~15L;
    const long SF = pow2_stride(16L * PW) / 4;   // 槽距（float）
    float* P = alloc_aligned((size_t)NS * SF * 4 + 4096);
    float* Rb = alloc_aligned((size_t)(NY + 8) * RS * 4 + 4096);
    memset(P, 0, (size_t)NS * SF * 4);
    memset(Rb, 0, (size_t)(NY + 8) * RS * 4);
    const float* R = Rb;
    const long sht = (((m4 - 1) & 15) + 1) * 4;
    sme_start();
    sme_zero_za();
    long Y = 0;
    for (int w = 0; w < 2; w++) {
        long it = w == 0 ? iters / 10 : iters;
        double t0 = now2();
        for (long i = 0; i < it; i++) {
            long nsl = rotate_slots > 1 ? rotate_slots : NS;
            long slot = rotate_slots ? (Y % nsl) : 0;
            long Yr = rotate_R ? (Y % NS) : 0;
            const float* prow = P + slot * SF;
            row_steps(nt, prow, prow + PW, prow + 2 * PW, prow + 3 * PW, R + Yr * RS, m4, rem, sht);
            Y++;
        }
        double t = now2() - t0;
        if (w == 1) {
            double cyc_call = t / it * 1.55e9;
            long steps = KW + 3;
            int nop = nt; (void)var;
            printf("  %-44s KW=%2d: %7.1f 周期/行  %5.2f 周期/步  (理想 %d)  效率 %5.1f%%\n", tag, KW, cyc_call, cyc_call / steps,
                   2 * nop, nop ? 100.0 * 2 * nop / (cyc_call / steps) : 0.0);
        }
    }
    sme_stop();
    free(P); free(Rb);
}

int main(int argc, char** argv)
{
    long iters = argc > 1 ? atol(argv[1]) : 100000;
    setvbuf(stdout, NULL, _IONBF, 0);
    int kws[] = {39, 55, 81};
    for (int ki = 0; ki < 3; ki++) {
        int KW = kws[ki];
        trial("固定行 固定 R nt4", KW, KW, 0, 0, 1, 4, iters);
        trial("全槽轮转 固定 R nt4", KW, KW, 1, 0, 1, 4, iters);
        trial("全槽轮转 + R 推进 nt4", KW, KW, 1, 1, 1, 4, iters);
        trial("全槽轮转 + R 推进 nt3", KW, KW, 1, 1, 1, 3, iters);
        trial("全槽轮转 + R 推进 nt2", KW, KW, 1, 1, 1, 2, iters);
        trial("全槽轮转 + R 推进 nt1", KW, KW, 1, 1, 1, 1, iters);
    }
    return 0;
}
