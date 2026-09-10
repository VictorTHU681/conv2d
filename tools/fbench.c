// 快速判题口径 bench：数据生成、校验调用、预热、计时与 bench_conv.c 完全一致，但参考结果只算一次，
// 缓存其 64 位哈希（refcache/H_W_KH_KW_nt.hash），之后每次调用（校验 + 每个计时轮次）都做逐位哈希比对。
// gcc -O3 -march=armv9-a+sme+sve2 -fopenmp fbench.c conv2d.c -o fbench -lm
// 用法：fbench H W KH KW [runs=3] [refcache_dir=./refcache]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <omp.h>
#include <sys/stat.h>

typedef float CONVFLOAT;
typedef int CONVINT;
void conv2d(const CONVFLOAT*, CONVINT, CONVINT, const CONVFLOAT*, CONVINT, CONVINT, CONVFLOAT*);

static CONVFLOAT rand_lcg(int* localSeed)
{
    int high = *localSeed / 127773, low = *localSeed % 127773;
    int test = 16807 * low - 2836 * high;
    int value = test + ((test > 0) ? 0 : 2147483647);
    *localSeed = value;
    return (CONVFLOAT)value / (CONVFLOAT)2147483647.0;
}
static void random_fmatrix(CONVFLOAT* mat, CONVINT rows, CONVINT cols, CONVINT lds, int seed)
{
#pragma omp parallel
    {
        int localSeed = seed + omp_get_thread_num();
#pragma omp for
        for (CONVINT i = 0; i < rows; ++i)
            for (CONVINT j = 0; j < cols; ++j) mat[i * lds + j] = rand_lcg(&localSeed);
    }
}
static void reference_conv2d(const CONVFLOAT* input, CONVINT H, CONVINT W, const CONVFLOAT* kernel, CONVINT KH, CONVINT KW, CONVFLOAT* output)
{
    const CONVINT oH = H - KH + 1, oW = W - KW + 1;
    memset(output, 0, (size_t)oH * oW * sizeof(CONVFLOAT));
#pragma omp parallel for
    for (CONVINT j = 0; j < oH; ++j)
        for (CONVINT i = 0; i < oW; ++i)
            for (CONVINT jk = 0; jk < KH; ++jk)
                for (CONVINT ik = 0; ik < KW; ++ik)
                    output[j * oW + i] += input[(j + jk) * W + (i + ik)] * kernel[jk * KW + ik];
}
// 64 位哈希（按 8 字节字，并行分段再合并；位精确判定用）
static uint64_t hash_buf(const void* p, size_t bytes)
{
    const uint64_t* w = (const uint64_t*)p;
    const size_t n = bytes / 8;
    const int nseg = 64;
    uint64_t seg[64];
#pragma omp parallel for
    for (int s = 0; s < nseg; s++) {
        uint64_t h = 0x9E3779B97F4A7C15ull ^ (uint64_t)s;
        for (size_t i = (size_t)s * n / nseg; i < (size_t)(s + 1) * n / nseg; i++) {
            h ^= w[i]; h *= 0x100000001B3ull; h ^= h >> 29;
        }
        seg[s] = h;
    }
    uint64_t h = 0xcbf29ce484222325ull;
    for (int s = 0; s < nseg; s++) { h ^= seg[s]; h *= 0x100000001B3ull; h ^= h >> 31; }
    return h;
}

int main(int argc, char** argv)
{
    if (argc < 5) { fprintf(stderr, "用法: fbench H W KH KW [runs] [cachedir]\n"); return 1; }
    const CONVINT H = atoi(argv[1]), W = atoi(argv[2]), KH = atoi(argv[3]), KW = atoi(argv[4]);
    const int runs = argc > 5 ? atoi(argv[5]) : 3;
    const char* cdir = argc > 6 ? argv[6] : "./refcache";
    const CONVINT oH = H - KH + 1, oW = W - KW + 1;
    const size_t obytes = (size_t)oH * oW * sizeof(CONVFLOAT);
    const int nt = omp_get_max_threads();

    CONVFLOAT* input = malloc((size_t)H * W * sizeof(CONVFLOAT));
    CONVFLOAT* kernel = malloc((size_t)KH * KW * sizeof(CONVFLOAT));
    CONVFLOAT* output = malloc(obytes);
    CONVFLOAT* check = malloc(obytes);
    random_fmatrix(input, H, W, W, 12345);
    random_fmatrix(kernel, KH, KW, KW, 67890);
    random_fmatrix(output, oH, oW, oW, 13579);     // 与官方一致：output 预填随机值（参考会 memset 清零）

    // 参考哈希：缓存命中则直接读；否则算一次官方参考并写入缓存
    char path[512]; snprintf(path, sizeof(path), "%s/%d_%d_%d_%d_nt%d.hash", cdir, H, W, KH, KW, nt);
    uint64_t ref_hash = 0; int have = 0;
    FILE* f = fopen(path, "r");
    if (f) { have = (fscanf(f, "%llx", (unsigned long long*)&ref_hash) == 1); fclose(f); }
    if (!have) {
        double t0 = omp_get_wtime();
        CONVFLOAT* ref = malloc(obytes);
        memcpy(ref, output, obytes);
        reference_conv2d(input, H, W, kernel, KH, KW, ref);
        ref_hash = hash_buf(ref, obytes);
        free(ref);
        mkdir(cdir, 0755);
        f = fopen(path, "w");
        if (f) { fprintf(f, "%016llx\n", (unsigned long long)ref_hash); fclose(f); }
        fprintf(stderr, "[fbench] 参考计算 %.1f s，哈希 %016llx 已缓存到 %s\n", omp_get_wtime() - t0, (unsigned long long)ref_hash, path);
    }

    // 校验调用（同官方：第一次调用）
    memcpy(check, output, obytes);
    conv2d(input, H, W, kernel, KH, KW, check);
    int ok = hash_buf(check, obytes) == ref_hash;
    free(check);
    if (!ok) {
        printf("%6d x%6d %6d x%6d %12s %12s %8s\n", H, W, KH, KW, "/", "/", "FAIL(hash)");
        return 2;
    }
    // 预热（同官方）
    {
        CONVFLOAT* oc = malloc(obytes); memcpy(oc, output, obytes);
        conv2d(input, H, W, kernel, KH, KW, oc); free(oc);
    }
    // 计时：每轮独立报告 + 每轮结果也做哈希校验
    double total = 0, best = 1e30;
    const double flops = (double)oH * oW * KH * KW * 2;
    for (int r = 0; r < runs; r++) {
        CONVFLOAT* oc = malloc(obytes); memcpy(oc, output, obytes);
        double t0 = omp_get_wtime();
        conv2d(input, H, W, kernel, KH, KW, oc);
        double t = omp_get_wtime() - t0;
        int rok = hash_buf(oc, obytes) == ref_hash;
        free(oc);
        total += t; if (t < best) best = t;
        printf("%6d x%6d %6d x%6d run%d %8.3f ms %10.1f GFLOPS %s\n", H, W, KH, KW, r, t * 1e3, flops / t * 1e-9, rok ? "PASS" : "FAIL(hash)");
        if (!rok) ok = 0;
    }
    printf("%6d x%6d %6d x%6d best %8.3f ms %10.1f GFLOPS | avg %8.3f ms %10.1f GFLOPS  %s\n", H, W, KH, KW,
           best * 1e3, flops / best * 1e-9, total / runs * 1e3, flops / (total / runs) * 1e-9, ok ? "PASS" : "FAIL");
    free(input); free(kernel); free(output);
    return ok ? 0 : 2;
}
