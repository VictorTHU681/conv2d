// 快速计时驱动（不做参考校验）：与 bench_conv.c 相同的分配/预热/计时方式
// gcc -O3 -march=armv9-a+sme+sve2 -fopenmp drv.c conv2d.c -o drv -lm
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
typedef float CONVFLOAT;
typedef int CONVINT;
void conv2d(const CONVFLOAT*, CONVINT, CONVINT, const CONVFLOAT*, CONVINT, CONVINT, CONVFLOAT*);

static CONVFLOAT rand_lcg(int* s)
{
    int high = *s / 127773, low = *s % 127773;
    int test = 16807 * low - 2836 * high;
    int value = test + ((test > 0) ? 0 : 2147483647);
    *s = value;
    return (CONVFLOAT)value / (CONVFLOAT)2147483647.0;
}
static void random_fmatrix(CONVFLOAT* mat, CONVINT rows, CONVINT cols, int seed)
{
#pragma omp parallel
    {
        int localSeed = seed + omp_get_thread_num();
#pragma omp for
        for (CONVINT i = 0; i < rows; ++i)
            for (CONVINT j = 0; j < cols; ++j) mat[(long)i * cols + j] = rand_lcg(&localSeed);
    }
}

int main(int argc, char** argv)
{
    int H = atoi(argv[1]), W = atoi(argv[2]), KH = atoi(argv[3]), KW = atoi(argv[4]);
    int runs = argc > 5 ? atoi(argv[5]) : 3;
    long outH = H - KH + 1, outW = W - KW + 1;
    CONVFLOAT* in = malloc((size_t)H * W * sizeof(CONVFLOAT));
    CONVFLOAT* k = malloc((size_t)KH * KW * sizeof(CONVFLOAT));
    CONVFLOAT* out = malloc(outH * outW * sizeof(CONVFLOAT));
    random_fmatrix(in, H, W, 12345);
    random_fmatrix(k, KH, KW, 67890);
    random_fmatrix(out, outH, outW, 13579);
    // 与基准一致：首次调用（校验）+ 预热
    CONVFLOAT* oc = malloc(outH * outW * sizeof(CONVFLOAT));
    memcpy(oc, out, outH * outW * sizeof(CONVFLOAT));
    conv2d(in, H, W, k, KH, KW, oc);
    free(oc);
    oc = malloc(outH * outW * sizeof(CONVFLOAT));
    memcpy(oc, out, outH * outW * sizeof(CONVFLOAT));
    conv2d(in, H, W, k, KH, KW, oc);
    free(oc);
    double best = 1e9, sum = 0;
    double flops = 2.0 * outH * outW * KH * KW;
    for (int r = 0; r < runs; r++) {
        oc = malloc(outH * outW * sizeof(CONVFLOAT));
        memcpy(oc, out, outH * outW * sizeof(CONVFLOAT));
        double t0 = omp_get_wtime();
        conv2d(in, H, W, k, KH, KW, oc);
        double t = omp_get_wtime() - t0;
        free(oc);
        sum += t;
        if (t < best) best = t;
    }
    printf("%5d x%5d k%3d: best %8.3f ms = %8.1f GFLOPS | avg %8.3f ms = %8.1f GFLOPS\n", H, W, KH, best * 1e3,
           flops / best * 1e-9, sum / runs * 1e3, flops / (sum / runs) * 1e-9);
    return 0;
}
