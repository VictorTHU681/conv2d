// 输出回写的 DRAM 流量探针：普通存储（RFO 读 + 写）vs dc zva 预清零后存储（应只剩写）vs 非时序存储 stnt1w。
// 38 线程各写 W 字节的独立区域（64 B 对齐，整线），统计有效写带宽；zva 若能免 RFO，带宽应明显高于普通存储。
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <omp.h>
#include <sys/mman.h>
#include <time.h>

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + 1e-9 * t.tv_nsec; }

__attribute__((target("+sve")))
static void store_plain(char* p, long n)   // n 字节，64 B 对齐，每线程顺序写
{
    for (long i = 0; i < n; i += 256)
        asm volatile("ptrue p0.s\n\t"
                     "st1w {z0.s}, p0, [%0]\n\t st1w {z0.s}, p0, [%0, #1, mul vl]\n\t"
                     "st1w {z0.s}, p0, [%0, #2, mul vl]\n\t st1w {z0.s}, p0, [%0, #3, mul vl]\n\t" :: "r"(p + i) : "memory", "p0");
}
__attribute__((target("+sve")))
static void store_prf(char* p, long n)     // 先 pstl2keep 预取 4 KB 之后的线（模拟内核的输出预取），再写
{
    for (long i = 0; i < n; i += 256)
        asm volatile("ptrue p0.s\n\t"
                     "prfm pstl2keep, [%0, #4096]\n\t prfm pstl2keep, [%0, #4160]\n\t prfm pstl2keep, [%0, #4224]\n\t prfm pstl2keep, [%0, #4288]\n\t"
                     "st1w {z0.s}, p0, [%0]\n\t st1w {z0.s}, p0, [%0, #1, mul vl]\n\t"
                     "st1w {z0.s}, p0, [%0, #2, mul vl]\n\t st1w {z0.s}, p0, [%0, #3, mul vl]\n\t" :: "r"(p + i) : "memory", "p0");
}
__attribute__((target("+sve")))
static void store_zva(char* p, long n)     // dc zva 清零 4 线后立即写（内核里 zva 会提前几块做）
{
    for (long i = 0; i < n; i += 256)
        asm volatile("ptrue p0.s\n\t"
                     "dc zva, %0\n\t add x9, %0, #64\n\t dc zva, x9\n\t add x9, %0, #128\n\t dc zva, x9\n\t add x9, %0, #192\n\t dc zva, x9\n\t"
                     "st1w {z0.s}, p0, [%0]\n\t st1w {z0.s}, p0, [%0, #1, mul vl]\n\t"
                     "st1w {z0.s}, p0, [%0, #2, mul vl]\n\t st1w {z0.s}, p0, [%0, #3, mul vl]\n\t" :: "r"(p + i) : "memory", "p0", "x9");
}
__attribute__((target("+sve")))
static void store_zva_ahead(char* p, long n)   // zva 领先 4 KB（更接近内核：先清零、几块后再写）
{
    for (long i = 0; i < 4096; i += 64) asm volatile("dc zva, %0" :: "r"(p + i) : "memory");
    for (long i = 0; i < n; i += 256) {
        if (i + 4096 + 256 <= n)
            asm volatile("add x9, %0, #4096\n\t dc zva, x9\n\t add x9, x9, #64\n\t dc zva, x9\n\t add x9, x9, #64\n\t dc zva, x9\n\t add x9, x9, #64\n\t dc zva, x9\n\t" :: "r"(p + i) : "memory", "x9");
        asm volatile("ptrue p0.s\n\t"
                     "st1w {z0.s}, p0, [%0]\n\t st1w {z0.s}, p0, [%0, #1, mul vl]\n\t"
                     "st1w {z0.s}, p0, [%0, #2, mul vl]\n\t st1w {z0.s}, p0, [%0, #3, mul vl]\n\t" :: "r"(p + i) : "memory", "p0");
    }
}
__attribute__((target("+sve")))
static void store_nt(char* p, long n)
{
    for (long i = 0; i < n; i += 256)
        asm volatile("ptrue p0.s\n\t"
                     "stnt1w {z0.s}, p0, [%0]\n\t stnt1w {z0.s}, p0, [%0, #1, mul vl]\n\t"
                     "stnt1w {z0.s}, p0, [%0, #2, mul vl]\n\t stnt1w {z0.s}, p0, [%0, #3, mul vl]\n\t" :: "r"(p + i) : "memory", "p0");
}
static void read_seq(const char* p, long n, volatile long* sink)   // 读带宽参照
{
    long s = 0;
    for (long i = 0; i < n; i += 64) s += *(const volatile long*)(p + i);
    *sink = s;
}

int main(int argc, char** argv)
{
    const long per = argc > 1 ? atol(argv[1]) : (64L << 20);   // 每线程字节数（默认 64 MB → 38 线程 2.4 GB）
    uint64_t dczid; asm volatile("mrs %0, dczid_el0" : "=r"(dczid));
    printf("DCZID_EL0 = 0x%lx: zva 块 %ld B, %s\n", (unsigned long)dczid, 4L << (dczid & 0xf), (dczid & 0x10) ? "禁止" : "允许");
    int T = omp_get_max_threads();
    char* buf = mmap(NULL, (size_t)per * T + 4096, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    memset(buf, 1, (size_t)per * T);   // 触碰全部页
    volatile long sink = 0;
    const char* names[] = {"读（参照）", "普通 st1w", "pstl2keep 预取 + st1w", "dc zva 紧接 st1w", "dc zva 领先 4 KB + st1w", "stnt1w 非时序"};
    for (int rep = 0; rep < 2; rep++)
    for (int m = 0; m < 6; m++) {
        double t0 = now();
        #pragma omp parallel
        {
            char* p = buf + (size_t)per * omp_get_thread_num();
            switch (m) {
            case 0: read_seq(p, per, &sink); break;
            case 1: store_plain(p, per); break;
            case 2: store_prf(p, per); break;
            case 3: store_zva(p, per); break;
            case 4: store_zva_ahead(p, per); break;
            case 5: store_nt(p, per); break;
            }
        }
        double dt = now() - t0;
        printf("  %-26s %7.2f ms  有效带宽 %6.1f GB/s\n", names[m], dt * 1e3, (double)per * T / dt / 1e9);
    }
    return 0;
}
