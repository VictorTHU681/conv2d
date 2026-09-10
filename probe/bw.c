// 38 线程访存带宽：读 / 写 / 非临时写 / 读+写（conv 形态：读输入 100 MB、写输出 100 MB）
// gcc -O2 -march=armv9-a+sve2 -fopenmp bw.c -o bw ; OMP_PROC_BIND=close OMP_PLACES=cores numactl -N 1 [-m 17] ./bw
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#include <arm_sve.h>

static float* alloc_touch(size_t n)
{
    float* p = aligned_alloc(4096, n * sizeof(float));
#pragma omp parallel for schedule(static)
    for (size_t i = 0; i < n; i += 1024) memset(p + i, 0, (n - i < 1024 ? n - i : 1024) * sizeof(float));
    return p;
}

int main(int argc, char** argv)
{
    size_t n = (argc > 1 ? atol(argv[1]) : 4096L * 6144);   // 元素数（≈100 MB）
    int reps = argc > 2 ? atoi(argv[2]) : 5;
    float* in = alloc_touch(n);
    float* out = alloc_touch(n);
    for (size_t i = 0; i < n; i += 4096) in[i] = 1.0f;
    int nth = omp_get_max_threads();
    printf("threads=%d  bytes/buf=%.1f MB\n", nth, n * 4.0 / 1e6);
    const char* names[] = {"read", "write st1w", "write stnt1w", "read+write st1w", "read+write stnt1w", "memcpy"};
    for (int mode = 0; mode < 6; mode++) {
        double best = 1e9;
        for (int r = 0; r < reps; r++) {
            double t0 = omp_get_wtime();
            float sink = 0;
#pragma omp parallel reduction(+ : sink)
            {
                int tid = omp_get_thread_num(), nt = omp_get_num_threads();
                size_t lo = n * tid / nt, hi = n * (tid + 1) / nt;
                lo &= ~(size_t)15; if (tid == nt - 1) hi = n; else hi &= ~(size_t)15;
                svbool_t pg = svptrue_b32();
                svfloat32_t acc = svdup_f32(0);
                switch (mode) {
                case 0:
                    for (size_t i = lo; i + 16 <= hi; i += 16) acc = svadd_f32_x(pg, acc, svld1_f32(pg, in + i));
                    break;
                case 1:
                    for (size_t i = lo; i + 16 <= hi; i += 16) svst1_f32(pg, out + i, acc);
                    break;
                case 2:
                    for (size_t i = lo; i + 16 <= hi; i += 16) svstnt1_f32(pg, out + i, acc);
                    break;
                case 3:
                    for (size_t i = lo; i + 16 <= hi; i += 16) svst1_f32(pg, out + i, svmul_f32_x(pg, svld1_f32(pg, in + i), svdup_f32(2.0f)));
                    break;
                case 4:
                    for (size_t i = lo; i + 16 <= hi; i += 16) svstnt1_f32(pg, out + i, svmul_f32_x(pg, svld1_f32(pg, in + i), svdup_f32(2.0f)));
                    break;
                case 5:
                    memcpy(out + lo, in + lo, (hi - lo) * sizeof(float));
                    break;
                }
                sink += svaddv_f32(pg, acc);
            }
            double t = omp_get_wtime() - t0;
            if (t < best) best = t;
            if (sink == 12345.0f) printf("x");
        }
        double bytes = (mode == 0 || mode == 1 || mode == 2) ? n * 4.0 : n * 8.0;
        printf("  %-20s %7.3f ms  %7.1f GB/s\n", names[mode], best * 1e3, bytes / best * 1e-9);
    }
    return 0;
}
