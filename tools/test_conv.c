// 泛化正确性测试：随机尺寸/核大小，与参考四重循环（同编译选项 → fmla）逐位比较
// gcc -O3 -march=armv9-a+sme+sve2 -fopenmp test_conv.c conv2d.c -o test_conv -lm
// TEST_BITWISE=1: require exact float bits; TEST_SIGNED=1: cancellation inputs;
// TEST_REUSE_HEIGHT=1: keep the kernel fixed across increasing input heights.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <omp.h>

typedef float CONVFLOAT;
typedef int CONVINT;
void conv2d(const CONVFLOAT* input, CONVINT inputHeight, CONVINT inputWidth,
            const CONVFLOAT* kernel, CONVINT kernelHeight, CONVINT kernelWidth, CONVFLOAT* output);

static CONVFLOAT rand_lcg(int* s)
{
    int high = *s / 127773, low = *s % 127773;
    int test = 16807 * low - 2836 * high;
    int value = test + ((test > 0) ? 0 : 2147483647);
    *s = value;
    return (CONVFLOAT)value / (CONVFLOAT)2147483647.0;
}

__attribute__((noinline)) static void reference(const CONVFLOAT* input, CONVINT inputHeight, CONVINT inputWidth,
                                                const CONVFLOAT* kernel, CONVINT kernelHeight, CONVINT kernelWidth,
                                                CONVFLOAT* output)
{
    const CONVINT outputHeight = inputHeight - kernelHeight + 1;
    const CONVINT outputWidth = inputWidth - kernelWidth + 1;
    memset(output, 0, (size_t)outputHeight * outputWidth * sizeof(CONVFLOAT));
#pragma omp parallel for
    for (CONVINT j = 0; j < outputHeight; ++j)
        for (CONVINT i = 0; i < outputWidth; ++i)
            for (CONVINT jk = 0; jk < kernelHeight; ++jk)
                for (CONVINT ik = 0; ik < kernelWidth; ++ik)
                    output[j * outputWidth + i] += input[(j + jk) * inputWidth + (i + ik)] * kernel[jk * kernelWidth + ik];
}

static int run_case(int H, int W, int KH, int KW, int seed, int verbose)
{
    long outH = H - KH + 1, outW = W - KW + 1;
    CONVFLOAT* in = malloc((size_t)H * W * sizeof(CONVFLOAT));
    CONVFLOAT* k = malloc((size_t)KH * KW * sizeof(CONVFLOAT));
    CONVFLOAT* o1 = malloc((size_t)outH * outW * sizeof(CONVFLOAT));
    CONVFLOAT* o2 = malloc((size_t)outH * outW * sizeof(CONVFLOAT));
    int s = seed;
    for (long i = 0; i < (long)H * W; i++) in[i] = rand_lcg(&s);
    if (getenv("TEST_REUSE_HEIGHT")) s = seed + 7919;
    for (long i = 0; i < (long)KH * KW; i++) k[i] = rand_lcg(&s);
    if (getenv("TEST_SIGNED")) {
        for (long i = 0; i < (long)H * W; i++) in[i] = 2.0f * in[i] - 1.0f;
        for (long i = 0; i < (long)KH * KW; i++) k[i] = 2.0f * k[i] - 1.0f;
    }
    for (long i = 0; i < outH * outW; i++) { o1[i] = 7.0f; o2[i] = 7.0f; }   // 初值无关（参考先清零）
    reference(in, H, W, k, KH, KW, o1);
    conv2d(in, H, W, k, KH, KW, o2);
    long nbad = 0;
    long bitdiff = 0;
    const int bitwise = getenv("TEST_BITWISE") != NULL;
    double maxerr = 0;
    for (long i = 0; i < outH * outW; i++) {
        double e = fabs((double)o1[i] - (double)o2[i]);
        int different = memcmp(o1 + i, o2 + i, sizeof(float)) != 0;
        bitdiff += different;
        if (!(e <= 1e-5) || (bitwise && different)) {
            static long nshow = -1; if (nshow < 0) { const char* e2 = getenv("TEST_SHOW"); nshow = e2 ? atol(e2) : 3; }
            if (nbad < nshow && verbose) printf("    mismatch @%ld (%ld,%ld): ref %.8g got %.8g\n", i, i / outW, i % outW, o1[i], o2[i]);
            nbad++;
        }
        if (e > maxerr) maxerr = e;
    }
    if (nbad || verbose)
        printf("  %4d x%4d  k %3d x%3d : %s  maxerr %.3g  bad %ld/%ld  bitdiff %ld\n", H, W, KH, KW, nbad ? "FAIL" : "ok", maxerr, nbad, outH * outW, bitdiff);
    free(in); free(k); free(o1); free(o2);
    return nbad == 0;
}

int main(int argc, char** argv)
{
    int n = argc > 1 ? atoi(argv[1]) : 200;
    int seed = argc > 2 ? atoi(argv[2]) : 1;
    int pass = 0, total = 0;
    // 固定边界用例
    int fixed[][4] = {{1, 1, 1, 1}, {5, 5, 5, 5}, {5, 300, 1, 1}, {300, 5, 1, 1}, {64, 64, 3, 3}, {70, 600, 7, 7},
                      {4, 1100, 1, 40}, {45, 45, 41, 41}, {100, 1200, 39, 39}, {300, 700, 39, 39}, {200, 2100, 81, 81},
                      {130, 530, 5, 81}, {130, 530, 81, 5}, {17, 1030, 3, 9}, {1030, 17, 9, 3}, {90, 320, 2, 2}};
    for (size_t i = 0; i < sizeof(fixed) / sizeof(fixed[0]); i++) {
        total++;
        pass += run_case(fixed[i][0], fixed[i][1], fixed[i][2], fixed[i][3], seed + (int)i, 1);
    }
    // 随机用例
    int s = seed * 7919 + 13;
    for (int t = 0; t < n; t++) {
        int KH = 1 + (int)(rand_lcg(&s) * 14), KW = 1 + (int)(rand_lcg(&s) * 14);
        if (t % 5 == 0) { KH = 30 + (int)(rand_lcg(&s) * 60); KW = 30 + (int)(rand_lcg(&s) * 60); }
        int H = KH + (int)(rand_lcg(&s) * 120), W = KW + (int)(rand_lcg(&s) * 1200);
        total++;
        pass += run_case(H, W, KH, KW, s, 0);
    }
    if (getenv("TEST_REUSE_HEIGHT")) {
        // Same kernel dimensions/output width, but increasing height. A cached
        // work partition must be rebuilt even though the packed kernel can fit.
        for (int h = 100; h <= 108; h += 4) {
            total++;
            pass += run_case(h, 1200, 81, 81, 51301, 1);
        }
    }
    printf("%s: %d/%d 通过\n", pass == total ? "ALL PASS" : "SOME FAIL", pass, total);
    return pass == total ? 0 : 1;
}
