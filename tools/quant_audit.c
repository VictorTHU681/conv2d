// Quantization feasibility survey, separate from the submitted implementation.
// Uses the benchmark's complete matrices and RNG, but samples output positions.
// Compile: gcc -O3 -fopenmp tools/quant_audit.c -o build/quant_audit -lm
#include <math.h>
#include <omp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static float random_value(int *seed)
{
    int v = 16807 * (*seed % 127773) - 2836 * (*seed / 127773);
    *seed = v + (v > 0 ? 0 : 2147483647);
    return (float)*seed / 2147483647.0f;
}

static void random_matrix(float *a, int h, int w, int seed)
{
#pragma omp parallel
    {
        int s = seed + omp_get_thread_num();
#pragma omp for
        for (int y = 0; y < h; ++y)
            for (int x = 0; x < w; ++x)
                a[(size_t)y * w + x] = random_value(&s);
    }
}

static float rounded_mantissa(float f, unsigned bits)
{
    uint32_t u;
    memcpy(&u, &f, sizeof u);
    unsigned drop = 23 - bits;
    u += ((1u << (drop - 1)) - 1) + ((u >> drop) & 1u);
    u &= ~((1u << drop) - 1);
    memcpy(&f, &u, sizeof f);
    return f;
}

static float quantize(float f, int mode)
{
    static const unsigned bits[] = {7, 10, 16, 20, 22};
    if (mode == 5) return (float)(_Float16)f;
    return rounded_mantissa(f, bits[mode]);
}

int main(int argc, char **argv)
{
    const int samples = argc > 1 ? atoi(argv[1]) : 256;
    if (samples < 4) return 2;
    const int cases[][3] = {{4096,6144,39},{6144,4096,41},
                            {4256,6390,55},{6390,4256,81}};
    const char *names[] = {"bf16", "mantissa10", "mantissa16", "mantissa20", "mantissa22", "fp16"};
    printf("threads=%d samples_per_case=%d tol=1e-5 reference=ordered_fmaf\n", omp_get_max_threads(), samples);
    for (int c = 0; c < 4; ++c) {
        const int h = cases[c][0], w = cases[c][1], k = cases[c][2];
        const int oh = h-k+1, ow = w-k+1;
        float *in = malloc((size_t)h*w*sizeof(float));
        float *kernel = malloc((size_t)k*k*sizeof(float));
        if (!in || !kernel) { free(in); free(kernel); return 2; }
        random_matrix(in,h,w,12345);
        random_matrix(kernel,k,k,67890);
        int bad[12] = {0}, s = 17001+c;
        double maxerr[12] = {0};
        for (int sample = 0; sample < samples; ++sample) {
            int y = sample < 4 ? (sample/2)*(oh-1) : (int)(random_value(&s)*(oh-1));
            int x = sample < 4 ? (sample%2)*(ow-1) : (int)(random_value(&s)*(ow-1));
            float ref = 0.0f, acc[12] = {0};
            for (int ky = 0; ky < k; ++ky) {
                for (int kx = 0; kx < k; ++kx) {
                    float a = in[(size_t)(y+ky)*w+x+kx], b = kernel[ky*k+kx];
                    ref = fmaf(a,b,ref);
                    for (int mode = 0; mode < 6; ++mode) {
                        float qb = quantize(b,mode);
                        acc[mode] = fmaf(a,qb,acc[mode]);
                        acc[6+mode] = fmaf(quantize(a,mode),qb,acc[6+mode]);
                    }
                }
            }
            for (int mode = 0; mode < 12; ++mode) {
                double err = fabs((double)acc[mode]-ref);
                bad[mode] += !(err <= 1e-5);
                if (err > maxerr[mode]) maxerr[mode] = err;
            }
        }
        for (int mode = 0; mode < 12; ++mode)
            printf("k=%d mode=%s operands=%s failed=%d/%d max_abs_error=%.9g\n",k,names[mode%6],mode<6?"kernel":"both",bad[mode],samples,maxerr[mode]);
        free(in); free(kernel);
    }
    return 0;
}
