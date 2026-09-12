// Link with -Wl,--wrap=posix_memalign -Wl,--wrap=free.
// Changing kernels must reuse large packing buffers after a full shape cycle.
#include <math.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void conv2d(const float*, int, int, const float*, int, int, float*);
int __real_posix_memalign(void**, size_t, size_t);
void __real_free(void*);
static struct { void* p; size_t n; } blocks[1024];
static size_t calls, live, peak;
int __wrap_posix_memalign(void** p, size_t alignment, size_t bytes)
{
    int rc = __real_posix_memalign(p, alignment, bytes);
    if (!rc) {
        calls++;
        for (int i = 0; i < 1024; i++) if (!blocks[i].p) {
            blocks[i].p = *p; blocks[i].n = bytes;
            live += bytes; if (live > peak) peak = live;
            return rc;
        }
        abort();
    }
    return rc;
}
void __wrap_free(void* p)
{
    if (p) for (int i = 0; i < 1024; i++) if (blocks[i].p == p) {
        live -= blocks[i].n; blocks[i].p = NULL; break;
    }
    __real_free(p);
}
int main(void)
{
    const int widths[] = {81, 39, 39, 55};
    float* in = malloc(100 * 400 * sizeof(float));
    float* k = malloc(81 * 81 * sizeof(float));
    float* out = malloc(20 * 400 * sizeof(float));
    float* ref = malloc(20 * 400 * sizeof(float));
    for (int i = 0; i < 100 * 400; i++) in[i] = (float)((i * 37 % 1021) - 510) / 511.0f;
    size_t warm_calls = 0;
    int ok = 1;
    for (int round = 0; round < 8; round++) {
        for (int c = 0; c < 4; c++) {
            int K = widths[c], H = K + 19, W = 400, ow = W - K + 1;
            // c==2 repeats the smaller kernel without changing any coefficient.
            if (c != 2) for (int i = 0; i < K*K; i++)
                k[i] = (float)((i * 17 + round * 13 + c * 7) % 509 - 254) / 255.0f;
#pragma omp parallel for
            for (int y = 0; y < 20; y++) for (int x = 0; x < ow; x++) {
                float sum = 0;
                for (int j = 0; j < K; j++) for (int i = 0; i < K; i++)
                    sum = fmaf(in[(y+j)*W+x+i], k[j*K+i], sum);
                ref[y*ow+x] = sum;
            }
            for (int i = 0; i < 20*ow; i++) out[i] = 7;
            conv2d(in, H, W, k, K, K, out);
            int equal = !memcmp(ref, out, 20*ow*sizeof(float));
            ok &= equal;
            printf("round=%d k=%d bitwise=%s aligned_calls=%zu live=%zu\n",
                   round, K, equal ? "PASS" : "FAIL", calls, live);
        }
        if (round == 0) warm_calls = calls;
    }
    printf("PACK_REUSE bitwise=%s extra_allocations=%zu peak_bytes=%zu %s\n",
           ok ? "PASS" : "FAIL", calls-warm_calls, peak,
           ok && calls == warm_calls ? "PASS" : "FAIL");
    free(in); free(k); free(out); free(ref);
    return ok && calls == warm_calls ? 0 : 1;
}
