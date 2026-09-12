// conv2d：二维 valid 卷积（相关）FP32，鲲鹏 SME 优化实现
//
// 位精确约束：校验容差 1e-5（绝对），而输出量级 ~KH*KW/4（数百到上千），FP32 一个 ulp 就超过容差，
// 因此每个输出必须与参考实现逐步相同：acc = fma(in, k, acc)，按 (jk, ik) 行主序累加（gcc -O3 默认
// -ffp-contract=fast 会把参考的 "+= a*b" 融合为 fmla）。SME 的 fmopa（非加宽 FP32）对每个 ZA 元素
// 正好是一次 fused multiply-add，所以可以把卷积映射成外积序列并保持逐步顺序。
//
// 映射（每个 ZA tile 16×16 FP32，4 个 tile）：
//   tile t、行 r、列 c=4*ic+jc  ↔  输出 (j0+3-jc, i0+64t+4r+3-ic)
//   步 (Y, X)（Y=0..KH+2, X=0..KW+2）：a_t[r] = in[j0+Y][i0+64t+4r+X]，b[c] = kpad[Y-3+jc][X-3+ic]
//   于是元素 (r,c) 在步 (Y,X) 累加 in[j+jk][i+ik]*k[jk][ik]，其中 jk=Y-3+jc、ik=X-3+ic，
//   越界的 kernel 位置补 0（fma(a,0,acc)=acc，位精确）。步序 Y 外 X 内 ⇒ 每个输出按 (jk,ik) 行主序累加。
//   代价：(KH+3)(KW+3)/(KH*KW) 的额外步数（39×39: 16%，81×81: 7.5%）。
// 供数：a 向量按列 stride 4 取输入 → 预先把输入行去交织为 4 个平面 plane_q[x] = in[row][4x+q]，
//   a_t 即 plane_q 上连续 16 个元素（q = X%4），每线程一个 L2 驻留的行环形缓冲（KH+3 槽，槽距 2 的幂不跨页）；
//   a 用 5 条 64B 对齐载入 + 4 条 ext（移位 4*(m mod 16) 字节）生成，避免非对齐载入（跨行 1.5 周期、命中 L2 时 2.5）；
//   b 向量由打包的 kernel R[Y][X'][jc] = kpad[Y-3+jc][X'-3] 连续取 16 个（行距 2 的幂）。
// 结构：一个 pass = 4 tile × (KH+3) 行，整个 Y 循环在一段汇编里（行间只有几条标量指令；行间 C 代码会抽空
//   fmopa 队列）；DRAM 预取（下一组输入行、本组输出行）与下一组平面的 ld4w 切片构建分散在各 4 步组末尾；
//   输出行 j0+3-jc 在第 KH-1+jc 行后已完成，jc=3/2/1 三行在 pass 最后三行内用 mova+st4w 存出（与 fmopa 交错），
//   回写前一行先把要写的线预取进 L1。按 pass 长度特化：KH+3 > 64（k81）时 DRAM 预取只进 L2、不做 pass 内回写。
//   工作项 = (列块, 4 行组)，静态加权划分 + relaxed CAS 窃取（release 会等 st4w 落地）；线程池在调用之间自旋。
//
// 编译：gcc -O3 [-march=armv9-a+sme+sve2] -fopenmp；运行期检测 SME(+FA64)，缺失时回退 SVE/标量通用实现。
// 可调环境变量（默认即最优）：CONV_SP 块宽 256*SP（0=自动）、CONV_POOL 线程池、CONV_SLICE 切片构建、
//   CONV_PFIN/CONV_PFOUT 预取、CONV_STORE 回写重叠、CONV_UZP 构建方式、CONV_PROFILE 分相计时（2 = 每线程）。
#define _GNU_SOURCE
// 若编译命令没给 -march（如题面的参考命令 gcc -O3 ...），在此打开 SME/SVE2（内联汇编与 SVE 内建函数都需要）；
// 编译器不认识 SME（GCC < 12）则退到通用实现（-DCONV_NO_SME_ASM 亦可强制）
#if !defined(CONV_NO_SME_ASM)
#  if defined(__aarch64__) && (defined(__ARM_FEATURE_SME) || __GNUC__ >= 12)
#    if !defined(__ARM_FEATURE_SME)
#      pragma GCC target("arch=armv9-a+sme+sve2")
#    endif
#  else
#    define CONV_NO_SME_ASM 1
#  endif
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stddef.h>
#include <sched.h>
#include <omp.h>
#include <sys/auxv.h>
#include <sys/mman.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <ucontext.h>
#ifdef __ARM_FEATURE_SVE
#include <arm_sve.h>
#endif

typedef float CONVFLOAT;
typedef int CONVINT;

#ifndef CONV_NO_SME_ASM
#define CONV_SME 1
#endif

// ---------------------------------------------------------------- 运行环境
#define HWCAP2_SME_BIT (1UL << 23)
#define HWCAP2_SME_FA64_BIT (1UL << 30)

static int sme_available(void)
{
    static int cached = -1;
    if (cached < 0) {
        unsigned long hw2 = getauxval(AT_HWCAP2);
        cached = ((hw2 & HWCAP2_SME_BIT) && (hw2 & HWCAP2_SME_FA64_BIT)) ? 1 : 0;
        const char* env = getenv("CONV_NO_SME");
        if (env && env[0] == '1') cached = 0;
    }
    return cached;
}

static int env_int(const char* name, int def)
{
    const char* s = getenv(name);
    return (s && *s) ? atoi(s) : def;
}

// 可调参数只在首次调用时读环境（getenv 每次要扫整个环境表，~2 µs/次，一次调用 9 次就是 ~0.3%）
typedef struct { int inited, slice, sp, prof, pf_in, pf_out, postart, uzp, poolwfe, pool, store_asm, pf_fresh, pf_l2, br, sw_dense, diag_l1, pf_st, zva, roll, roll_pd; } knobs_t;
static knobs_t g_knobs;
static int g_diag_on = 0;   // 线上诊断输出（见 diag_*）
#ifdef CONV_ROWPROF
static uint64_t* g_rowts = NULL;      // 线程 0 的逐行时间戳：行首 cntvct；pass 末追加 (cyc | 1<<63) 作结束标记
static uint64_t* g_rowts_cur = NULL;
static uint64_t* g_rowts_end = NULL;
#endif
static int g_pf_fresh = 1;
static void read_knobs(void)
{
    if (g_knobs.inited) return;
    g_knobs.slice = env_int("CONV_SLICE", 1);
    g_knobs.sp = env_int("CONV_SP", 0);
    g_knobs.prof = env_int("CONV_PROFILE", 0);
    g_knobs.pf_in = env_int("CONV_PFIN", 1);
    g_knobs.pf_out = env_int("CONV_PFOUT", 1);
    g_knobs.pf_st = env_int("CONV_PFST", 1);
    g_knobs.roll = env_int("CONV_ROLL", -1);        // 滚动 16×1 形态：-1 按形状自动，0 关，1 强制
    g_knobs.roll_pd = env_int("CONV_ROLL_PD", 3);   // 滚动形态的行预取提前量
    // -DCONV_ZVA_CURSOR 实验用：输出线 dc zva 预清零（不从 DRAM 读 RFO，每次调用少读 ~100 MB），需 zva 块 64 B 且允许
    { uint64_t dczid; asm volatile("mrs %0, dczid_el0" : "=r"(dczid));
      g_knobs.zva = env_int("CONV_ZVA", 1) && !(dczid & 0x10) && (4L << (dczid & 0xf)) == 64; }
    g_knobs.postart = env_int("CONV_POSTART", 0);
    g_knobs.uzp = env_int("CONV_UZP", 1);
    g_knobs.poolwfe = env_int("CONV_POOLWFE", 0);
    g_knobs.pool = env_int("CONV_POOL", 1);
    g_knobs.store_asm = env_int("CONV_STORE", -1); // 1: jc=3/2/1 行的回写与 pass 末三行的 fmopa 重叠；0: 全部由 C 回写；-1 自动
    g_knobs.pf_l2 = env_int("CONV_PFL2", -1);      // 1: DRAM 预取到 L2；0: L1；-1 自动（长 pass 用 L2）
    g_knobs.diag_l1 = env_int("CONV_DIAG_L1", 0);    // 诊断（结果错误）：1 a 数据 L1 驻留；2 a+b 都 L1 驻留
    g_knobs.pf_fresh = env_int("CONV_PFFRESH", 1); // 整环重建前先预取全部行
    g_knobs.br = env_int("CONV_BR", 1);            // 边界行 fmla 方案（0 关；1 自动选去掉的行数）
    g_knobs.sw_dense = env_int("CONV_SWDENSE", -1); // 半步密度：1 稠密 / 0 稀疏 / -1 按容量自动
#ifdef CONV_DIAG_ONLINE
    g_diag_on = env_int("CONV_DIAG", 1);
#else
    g_diag_on = env_int("CONV_DIAG", 0);
#endif

    g_pf_fresh = g_knobs.pf_fresh;
    g_knobs.inited = 1;
}

static cpu_set_t g_thr_mask[1024];
static int g_cpus[CPU_SETSIZE];
static int g_ncpu = -1;

// 可用 CPU 集 = 各线程亲和掩码的并集（兼容 numactl / taskset / OMP_PROC_BIND）
static void discover_cpus(void)
{
    if (g_ncpu >= 0) return;
#pragma omp parallel
    {
        int tid = omp_get_thread_num();
        int nt = omp_get_num_threads();
        if (tid < 1024) sched_getaffinity(0, sizeof(cpu_set_t), &g_thr_mask[tid]);
#pragma omp barrier
#pragma omp single
        {
            cpu_set_t u;
            CPU_ZERO(&u);
            int lim = nt < 1024 ? nt : 1024;
            for (int t = 0; t < lim; t++) CPU_OR(&u, &u, &g_thr_mask[t]);
            int n = 0;
            for (int c = 0; c < CPU_SETSIZE; c++) if (CPU_ISSET(c, &u)) g_cpus[n++] = c;
            g_ncpu = n;
        }
    }
}

static inline void pin_self(int tid)
{
    if (g_ncpu > 0 && tid < g_ncpu) {
        cpu_set_t s;
        CPU_ZERO(&s);
        CPU_SET(g_cpus[tid], &s);
        sched_setaffinity(0, sizeof(s), &s);
    }
}


// ---------------------------------------------------------------- 通用实现（SVE，按列向量化，位精确）
static void conv2d_generic(const CONVFLOAT* in, CONVINT H, CONVINT W, const CONVFLOAT* k, CONVINT KH, CONVINT KW,
                           CONVFLOAT* out)
{
    const long outH = H - KH + 1, outW = W - KW + 1;
#pragma omp parallel for schedule(static)
    for (long j = 0; j < outH; ++j) {
        CONVFLOAT* orow = out + j * outW;
#ifdef __ARM_FEATURE_SVE
        long i = 0;
        const long VL = svcntw();
        for (; i < outW; i += VL) {
            svbool_t pg = svwhilelt_b32((int64_t)i, (int64_t)outW);
            svfloat32_t acc = svdup_f32(0.0f);
            for (long jk = 0; jk < KH; ++jk) {
                const CONVFLOAT* irow = in + (j + jk) * (long)W + i;
                const CONVFLOAT* krow = k + jk * (long)KW;
                for (long ik = 0; ik < KW; ++ik)
                    acc = svmla_n_f32_x(pg, acc, svld1_f32(pg, irow + ik), krow[ik]);
            }
            svst1_f32(pg, orow + i, acc);
        }
#else
        for (long i = 0; i < outW; ++i) {
            float acc = 0.0f;
            for (long jk = 0; jk < KH; ++jk)
                for (long ik = 0; ik < KW; ++ik) acc = __builtin_fmaf(in[(j + jk) * (long)W + i + ik], k[jk * KW + ik], acc);
            orow[i] = acc;
        }
#endif
    }
}

#ifdef CONV_SME
// ---------------------------------------------------------------- SME 内核
#define VCLOB "z0","z1","z2","z3","z4","z5","z6","z7","z8","z9","z10","z11","z12","z13","z14","z15","z16","z17","z18","z19","z20","z21","z22","z23","z24","z25","z26","z27","z28","z29","z30","z31"
#define PCLOB "p0","p1","p2","p3","p4","p5","p6","p7","p8","p9","p10","p11","p12","p13","p14","p15"

static inline uint64_t cyc(void) { uint64_t v; asm volatile("mrs %0, cntvct_el0" : "=r"(v)); return v; }
static inline uint64_t cyc_hz(void) { uint64_t v; asm volatile("mrs %0, cntfrq_el0" : "=r"(v)); return v; }
typedef struct { uint64_t build, kern, store, total, enter, items, steals, cpu; } prof_t;

static inline void sme_start(void) { asm volatile("smstart\n\t" ::: "memory", VCLOB, PCLOB); }
static inline void sme_stop(void) { asm volatile("smstop\n\t" ::: "memory", VCLOB, PCLOB); }
static inline void sme_zero_za(void) { asm volatile("zero {za}\n\t" ::: "memory"); }


// ---- 线上诊断（编译期 -DCONV_DIAG_ONLINE 或环境 CONV_DIAG=1；输出到 stdout，供评测机日志回看）
//  每次调用：分相计时 + 各线程末尾的主频（8 条相依 add 链，cntvct 计时）；第 2 次调用（基准的预热，不计时）另测：
//  起始主频、fmopa 吞吐（4 tile 轮转，期望 2 周期/条）、38 线程 DRAM 带宽（读 / 整线写 / pstl2keep 预取+写 / stnt1w）
typedef struct { double ghz0, ghz1, ghz_fm, fmopa_ns, fmopa_ns2, fm_half, fm_quarter, ghz_half, t_rd, t_wr, t_pfwr, t_nt; uint64_t c0, c1; } diag_t;
static diag_t g_diag[1024];
static volatile uint64_t g_diag_bar __attribute__((aligned(64)));
static inline double diag_ghz(long iters)   // 每次迭代 8 条相依 add = 8 周期
{
    uint64_t t0 = cyc(); uint64_t x = 0;
    asm volatile("1:\n\t add %0, %0, #1\n\t add %0, %0, #1\n\t add %0, %0, #1\n\t add %0, %0, #1\n\t"
                 "add %0, %0, #1\n\t add %0, %0, #1\n\t add %0, %0, #1\n\t add %0, %0, #1\n\t subs %1, %1, #1\n\t b.ne 1b\n\t"
                 : "+r"(x), "+r"(iters) : : "cc");
    uint64_t t1 = cyc();
    return (double)x / ((double)(t1 - t0) * 1e9 / (double)cyc_hz());
}
static inline double diag_fmopa_ns(long iters)   // 流式模式内：8 条 fmopa（4 tile × 2）/迭代
{
    const long n = iters;
    asm volatile("ptrue p0.s\n\t zero {za}\n\t" ::: "memory");
    uint64_t t0 = cyc();
    asm volatile("1:\n\t"
                 "fmopa za0.s, p0/m, p0/m, z0.s, z1.s\n\t fmopa za1.s, p0/m, p0/m, z0.s, z1.s\n\t"
                 "fmopa za2.s, p0/m, p0/m, z0.s, z1.s\n\t fmopa za3.s, p0/m, p0/m, z0.s, z1.s\n\t"
                 "fmopa za0.s, p0/m, p0/m, z0.s, z1.s\n\t fmopa za1.s, p0/m, p0/m, z0.s, z1.s\n\t"
                 "fmopa za2.s, p0/m, p0/m, z0.s, z1.s\n\t fmopa za3.s, p0/m, p0/m, z0.s, z1.s\n\t"
                 "subs %0, %0, #1\n\t b.ne 1b\n\t" : "+r"(iters) : : "cc", "memory");
    uint64_t t1 = cyc();
    return (double)(t1 - t0) * 1e9 / (double)cyc_hz() / (8.0 * (double)n);
}
static void diag_barrier(int nth, int phase)
{
    __atomic_add_fetch(&g_diag_bar, 1, __ATOMIC_ACQ_REL);
    while (__atomic_load_n(&g_diag_bar, __ATOMIC_ACQUIRE) < (uint64_t)nth * (uint64_t)phase) asm volatile("yield" ::: "memory");
}
// 每线程 16 MB 私有区（调用方在流式模式外 mmap+memset，因为系统调用会让内核退出流式模式并清 ZA）：4 种访问各计时（秒）
#define DIAG_BW_BYTES (16L << 20)
static void diag_bw(int nth, diag_t* d, char* buf)
{
    const long n = DIAG_BW_BYTES;
    const double tick = 1.0 / (double)cyc_hz();
    if (!buf) { d->t_rd = d->t_wr = d->t_pfwr = d->t_nt = 0; for (int ph = 4; ph <= 7; ph++) diag_barrier(nth, ph); return; }
    double t0, t1;
    diag_barrier(nth, 4); t0 = (double)cyc() * tick;
    { volatile long acc = 0; long sacc = 0; for (long i = 0; i < n; i += 64) sacc += *(volatile long*)(buf + i); acc = sacc; (void)acc; }
    t1 = (double)cyc() * tick; d->t_rd = t1 - t0;
    diag_barrier(nth, 5); t0 = (double)cyc() * tick;
    for (long i = 0; i < n; i += 256)
        asm volatile("ptrue p0.s\n\t st1w {z0.s}, p0, [%0]\n\t st1w {z0.s}, p0, [%0, #1, mul vl]\n\t st1w {z0.s}, p0, [%0, #2, mul vl]\n\t st1w {z0.s}, p0, [%0, #3, mul vl]\n\t" :: "r"(buf + i) : "memory", "p0");
    t1 = (double)cyc() * tick; d->t_wr = t1 - t0;
    diag_barrier(nth, 6); t0 = (double)cyc() * tick;
    for (long i = 0; i < n; i += 256)
        asm volatile("ptrue p0.s\n\t prfm pstl2keep, [%0, #4096]\n\t prfm pstl2keep, [%0, #4160]\n\t prfm pstl2keep, [%0, #4224]\n\t prfm pstl2keep, [%0, #4288]\n\t"
                     "st1w {z0.s}, p0, [%0]\n\t st1w {z0.s}, p0, [%0, #1, mul vl]\n\t st1w {z0.s}, p0, [%0, #2, mul vl]\n\t st1w {z0.s}, p0, [%0, #3, mul vl]\n\t" :: "r"(buf + i) : "memory", "p0");
    t1 = (double)cyc() * tick; d->t_pfwr = t1 - t0;
    diag_barrier(nth, 7); t0 = (double)cyc() * tick;
    for (long i = 0; i < n; i += 256)
        asm volatile("ptrue p0.s\n\t stnt1w {z0.s}, p0, [%0]\n\t stnt1w {z0.s}, p0, [%0, #1, mul vl]\n\t stnt1w {z0.s}, p0, [%0, #2, mul vl]\n\t stnt1w {z0.s}, p0, [%0, #3, mul vl]\n\t" :: "r"(buf + i) : "memory", "p0");
    t1 = (double)cyc() * tick; d->t_nt = t1 - t0;
}
static void diag_sigill(int sig, siginfo_t* si, void* uc_)
{
    ucontext_t* uc = (ucontext_t*)uc_;
    unsigned long pc = uc->uc_mcontext.pc;
    unsigned insn = *(volatile unsigned*)pc;
    char buf[160]; int n = snprintf(buf, sizeof buf, "[conv-diag] SIGILL sig %d code %d pc 0x%lx insn 0x%08x addr %p\n", sig, si->si_code, pc, insn, si->si_addr);
    if (write(1, buf, (size_t)n) < 0) {}
    _exit(132);
}
// 计时调用（第 3 次）的汇总不在函数内格式化/打印（printf 的浮点格式化 + 写 stdout 有 ~0.1 ms），只存原始数据，进程退出时打印
typedef struct { unsigned long call; long H, W, KH, KW; double region, pre, tn, ta, tx, g1n, g1a, g1x, total; } diag_sum_t;
static diag_sum_t g_diag_deferred[8];
static int g_diag_deferred_n = 0;
static double g_diag_thr_ms[1024]; static int g_diag_thr_n = 0;
static void diag_atexit(void)
{
    if (g_diag_thr_n) { printf("[conv-diag] thr total ms: "); for (int t = 0; t < g_diag_thr_n; t++) printf("%d:%.1f ", t, g_diag_thr_ms[t]); printf("\n"); }
    for (int i = 0; i < g_diag_deferred_n; i++) {
        const diag_sum_t* d = &g_diag_deferred[i];
        printf("[conv-diag] call %lu %ldx%ld k%ldx%ld: region %.3f ms | pre %.3f | thr total min/avg/max %.3f/%.3f/%.3f ms | ghz@end min/avg/max %.3f/%.3f/%.3f | conv2d() total %.3f ms\n",
               d->call, d->H, d->W, d->KH, d->KW, d->region, d->pre, d->tn, d->ta, d->tx, d->g1n, d->g1a, d->g1x, d->total);
    }
    fflush(stdout);
}
static void diag_read_line(const char* path, char* out, size_t n)
{
    out[0] = 0; FILE* f = fopen(path, "r"); if (!f) { snprintf(out, n, "?"); return; }
    if (!fgets(out, (int)n, f)) snprintf(out, n, "?");
    fclose(f);
    size_t l = strlen(out); while (l && (out[l - 1] == '\n' || out[l - 1] == ' ')) out[--l] = 0;
}
static void diag_print_env(int nth)
{
    char part[64] = "?", thp[96] = "?", cur[32] = "?", mx[32] = "?", gov[32] = "?", path[128];
    FILE* f = fopen("/proc/cpuinfo", "r");
    if (f) { char line[256]; while (fgets(line, sizeof line, f)) if (!strncmp(line, "CPU part", 8)) { char* c = strchr(line, ':'); if (c) snprintf(part, sizeof part, "%s", c + 2); part[strcspn(part, "\n")] = 0; break; } fclose(f); }
    diag_read_line("/sys/kernel/mm/transparent_hugepage/enabled", thp, sizeof thp);
    int cpu = sched_getcpu();
    snprintf(path, sizeof path, "/sys/devices/system/cpu/cpu%d/cpufreq/scaling_cur_freq", cpu); diag_read_line(path, cur, sizeof cur);
    snprintf(path, sizeof path, "/sys/devices/system/cpu/cpu%d/cpufreq/cpuinfo_max_freq", cpu); diag_read_line(path, mx, sizeof mx);
    snprintf(path, sizeof path, "/sys/devices/system/cpu/cpu%d/cpufreq/scaling_governor", cpu); diag_read_line(path, gov, sizeof gov);
    cpu_set_t cs; int ncpu = -1; if (sched_getaffinity(0, sizeof cs, &cs) == 0) ncpu = CPU_COUNT(&cs);
    uint64_t svl = 0, dczid = 0; asm volatile("rdsvl %0, #1" : "=r"(svl)); asm volatile("mrs %0, dczid_el0" : "=r"(dczid));
    printf("[conv-diag] env: threads %d | cpu part %s | affinity %d cpus, cpu0=%d | svl %lu B | dczid 0x%lx | cntfrq %lu | page %ld | thp %s | "
           "cpufreq cur %s max %s gov %s | nprocs %ld\n", nth, part, ncpu, cpu, (unsigned long)svl, (unsigned long)dczid, (unsigned long)cyc_hz(),
           (long)sysconf(_SC_PAGESIZE), thp, cur, mx, gov, (long)sysconf(_SC_NPROCESSORS_ONLN));
}

// 1×4 tile 排布：tile t ↔ 输出列 c0+64t..+63，4 个 tile 同一行组（j0..j0+3），共用 b 向量。
// 步 (Y, X)：输入行 j0+Y，a_t = plane_q[m + 16t + r]（q = X%4, m = X/4），b = R[Y][X]，4 条 fmopa 共 8 周期。
// a 向量按元素偏移 m 滑动 → 若直接非对齐载入（4 条/步），载入管线成为瓶颈（每条 1.5 周期，行在 L2 时 2.5）。
// 改为：5 条 64B 对齐载入 V0..V4 + 4 条 ext（按字节移位 4*(m mod 16)，1 条/周期且与 fmopa 并发）生成 a0..a3；
// m 每 16 步组推进一次对齐基址；移位量是立即数，因此把 16 个移位展开为 16 个块，尾步（rem）用非对齐载入。
// 相比 2×2（两个行组错开 4 行 → 每 pass 8 个只有一半 fmopa 的边界行 ≈ 10%），1×4 没有边界行且只有一条 b 流。
#define OPA(T, A, B) "fmopa za" #T ".s, p0/m, p0/m, z" #A ".s, z" #B ".s\n\t"
#define LDV(V, q, i) "ld1w {z" #V ".s}, p0/z, [%[p" #q "], #" #i ", mul vl]\n\t"
// 破坏式 ext：a_t 直接覆盖 V_t（V_t 之后不再用），主循环只占 6 个向量寄存器（z5..z10），
// 腾出 z0..z4 与 z16..z31 给边界行 fmla（探针：单寄存器组、fmla 与 ext 并发均无损）
#define EXT(V0, V1, sh) "ext z" #V0 ".b, z" #V0 ".b, z" #V1 ".b, #" #sh "\n\t"
#define LDB(B) "ld1w {z" #B ".s}, p0/z, [%[pb]]\n\t add %[pb], %[pb], #16\n\t"

// 向量寄存器分配：z0 fmla 的 kernel 四元组 | z1..z4 fmla 的 a | z5..z9 V0..V4（ext 后即 a0..a3）| z10 b |
//                 z11..z14 切片 ld4w / 回写 mova（不同块组，分时复用）| z16..z31 fmla 累加器（4 tile × 4 ic）
// 一步（平面 q，移位 sh 字节），nt = 4/3/2/1 个 tile
#define STEP4X(q, sh)                                                                       \
    LDB(10) LDV(5, q, 0) LDV(6, q, 1) LDV(7, q, 2) LDV(8, q, 3) LDV(9, q, 4)               \
    EXT(5, 6, sh) EXT(6, 7, sh) EXT(7, 8, sh) EXT(8, 9, sh)                                 \
    OPA(0, 5, 10) OPA(1, 6, 10) OPA(2, 7, 10) OPA(3, 8, 10)
#define STEP3X(q, sh)                                                                       \
    LDB(10) LDV(5, q, 0) LDV(6, q, 1) LDV(7, q, 2) LDV(8, q, 3)                            \
    EXT(5, 6, sh) EXT(6, 7, sh) EXT(7, 8, sh)                                               \
    OPA(0, 5, 10) OPA(1, 6, 10) OPA(2, 7, 10)
#define STEP2X(q, sh)                                                                       \
    LDB(10) LDV(5, q, 0) LDV(6, q, 1) LDV(7, q, 2)                                         \
    EXT(5, 6, sh) EXT(6, 7, sh)                                                             \
    OPA(0, 5, 10) OPA(1, 6, 10)
#define STEP1X(q, sh)                                                                       \
    LDB(10) LDV(5, q, 0) LDV(6, q, 1)                                                      \
    EXT(5, 6, sh)                                                                           \
    OPA(0, 5, 10)
// 一个 4 步组（q=0..3 同一移位），末尾：b 流预取、边界行 fmla 步、附加工作、计数并可能退出
#ifdef CONV_NOPFB
#define PFB_ROW
#else
#define PFB_ROW "prfm pldl1keep, [%[pb], #256]\n\t"
#endif
// 边界行 fmla 半步（8 条 fmla）插在步之间。块组按 (序号 mod 3) 分三型：A：步 0 之后（仅稠密）+ 步 3 之后；B：步 2 之后；
// C：步 1 之后 → 稠密 4 半步 / 12 步（2.67 fmla/步，均匀），稀疏 1 半步 / 块组（2 fmla/步）
// （探针：≤ 3.2 fmla/步、8 条一簇无开销；实测半步附近受指令发射带宽约束，越少指令越好）
#define EX_HALF_D "ldr x9, [%[a], #352]\n\t cbz x9, 79f\n\t" EX_HALF "79:\n\t"
#define BLOCKX_A(sh, STEP, EXTRA)                                                           \
    STEP(0, sh) EX_HALF_D STEP(1, sh) STEP(2, sh) STEP(3, sh) EX_HALF                       \
    PFB_ROW                                                                                 \
    EXTRA                                                                                   \
    "subs %[m], %[m], #1\n\t b.eq 9f\n\t"
#define BLOCKX_B(sh, STEP, EXTRA)                                                           \
    STEP(0, sh) STEP(1, sh) STEP(2, sh) EX_HALF STEP(3, sh)                                 \
    PFB_ROW                                                                                 \
    EXTRA                                                                                   \
    "subs %[m], %[m], #1\n\t b.eq 9f\n\t"
#define BLOCKX_C(sh, STEP, EXTRA)                                                           \
    STEP(0, sh) STEP(1, sh) EX_HALF STEP(2, sh) STEP(3, sh)                                 \
    PFB_ROW                                                                                 \
    EXTRA                                                                                   \
    "subs %[m], %[m], #1\n\t b.eq 9f\n\t"
// 尾步：非对齐载入（基址 = 对齐基址 + sht），nt 个 a
#define TL(A, xq, i) "ld1w {z" #A ".s}, p0/z, [" #xq ", #" #i ", mul vl]\n\t"
#define TAIL4(xq) LDB(10) TL(5, xq, 0) TL(6, xq, 1) TL(7, xq, 2) TL(8, xq, 3) OPA(0, 5, 10) OPA(1, 6, 10) OPA(2, 7, 10) OPA(3, 8, 10)
#define TAIL3(xq) LDB(10) TL(5, xq, 0) TL(6, xq, 1) TL(7, xq, 2) OPA(0, 5, 10) OPA(1, 6, 10) OPA(2, 7, 10)
#define TAIL2(xq) LDB(10) TL(5, xq, 0) TL(6, xq, 1) OPA(0, 5, 10) OPA(1, 6, 10)
#define TAIL1(xq) LDB(10) TL(5, xq, 0) OPA(0, 5, 10)

// 整个 pass 的 Y 循环都在一个 asm 里：行与行之间只有 ~10 条指令（槽表取址、b 行推进），
// DRAM 预取（下一组的原始输入行、本组输出行）用游标放在每行的第 0 个 4 步组里，与 fmopa 交错。
// （行间 C 代码每多 ~20 条指令，fmopa 队列就会被抽空一次，实测整体慢 3–7%。）
// 参数通过 pass_t 结构传入（字段偏移作立即数），游标/常量驻留在显式寄存器：
//   x12 槽表游标  x13 R 行指针  x14 剩余行数（= 回写行 jc，兼作 mova 切片索引）  x15 sweep 的 a 地址（0 = 空闲）
//   x16 下一行平面 0 基址（行首软流水）  x17 sweep 的 kernel 四元组地址
//   x19-x21 输入预取游标  x24-x26 输出预取游标  x22/x23/x27/x28 切片构建  x9-x11 临时
// 回写重叠：输出行 j0+3-jc 在 Y=KH-1+jc 后已完成（此后 b 的该列恒为 0，fmopa 只加 0），
//   因此 jc=3/2/1 三行分别在剩余行数 x14=3/2/1 的行内（块 6..9，每块一个 tile）用 mova+st4w 存出，
//   与 fmopa 交错；pass 结束后只剩 jc=0 一行暴露（回写相 0.09 → ~0.03 ms）。
typedef struct {
    const uint64_t* tab;       // 0  槽表游标（每项 = 平面 0 基址，字节地址）
    const float* pbrow;        // 8  R 行 0
    long Y;                    // 16 行数 NS
    const char* pi;            // 24 输入预取：下一线地址
    const char* pie;           // 32 当前段末（不含）
    long pin;                  // 40 剩余线数
    long ijump;                // 48 段末跳到下一行：+jump
    long istride;              // 56 段末推进：e += stride
    const char* po;            // 64 输出预取（同上）
    const char* poe;           // 72
    long pon;                  // 80
    long ojump;                // 88
    long ostride;              // 96
    long PWb;                  // 104 平面字节宽
    long RSB;                  // 112 R 行字节距
    long m4;                   // 120 每行 4 步组数
    long rem;                  // 128 尾步数
    long sht;                  // 136 尾步字节偏移
    const char* ssrc;          // 144 切片构建：哑行起点（真行 0 起点 - 256 - sjump）
    const uint64_t* stab;      // 152 切片构建：目标槽表（行 j0+NS+i 的槽基址）
    long snfull;               // 160 每行整切片数（64 列一片）
    long srows;                // 168 要构建的行数 + 1（哑行）；0 = 不做
    long sjump;                // 176 行末 src 跳转 = W*4 - snfull*256
    char* sdummy;              // 184 哑行目标：Y=0 期间槽 j0 还在被读，切片先写到这里
    long sdcnt;                // 192 哑行片数 = 每行 16 块组数（每个块组都会执行一次切片）
    long postart;              // 200 输出预取从"剩余行数 ≤ postart"时开始（太早预取会在回写前被挤出 L1）
    char* sdst[4];             // 208..232 tile t 输出行 j0（jc=3）的目标地址；NULL = 该 tile 不在 asm 内回写
    long sstr[4];              // 240..264 tile t 输出行距（字节）：行 jc 的地址 = sdst + (3-jc)*sstr
    long PW2b, PW3b;           // 272, 280 = 2*PWb, 3*PWb（行首三条 add 互不依赖）
    long poff;                 // 288 槽表项 → 本 pass 平面 0 基址的偏移（第 p 个 pass = 256*p 字节），免去每 pass 复制槽表
    char* pfst[4];             // 296..320 tile t 输出行 j0 的地址（回写前一行把该 tile 即将写的 4 线预取进 L1）；NULL = 不做
    long jcoff;                // 328 边界行方案：Y 循环少跑的尾行数 → 剩余行数 x14 对应的回写行 jc = x14 + jcoff
    // 边界行 fmla 扫描（sweep）状态：一个 sweep = 某输入行 Y'、某 kernel 行 kj，对 4 tile × 4 ic 的 16 个累加器
    // 走 X' = 0..KW+2；每个块组末尾走一步（4 条非对齐 a 载入 + ld1rqw + 16 条索引 fmla）
    char* sw_xc;               // 336 当前 a 地址（plane_q[m] + 64t 用 #t, mul vl）；0 = 无活动 sweep（asm 内驻留 x15）
    const char* sw_xk;         // 344 当前 kernel 四元组地址（Kp[kj][X']）（asm 内驻留 x17）
    long sw_dense;             // 352 1 → 每 8 步 3 个半步（3 fmla/步）；0 → 每块组 1 个半步（2 fmla/步）
    long sw_len;               // 360 每个 sweep 的字节长度 = 4*(KW+3)（kernel 四元组地址每步 +4）
    long inc[4];               // 368..392 a 地址增量表（按 X' mod 4）：+PWb ×3，然后 −3PWb+4
    const struct swd* swq;     // 400 当前 sweep 描述符；结束时取下一个（abase=0 终止）
    long sw_pad1[3];           // 408..424
    long sw_half;              // 432 半步标志：0 → 下一半步做 tile 0/1（并载四元组），1 → tile 2/3 并推进 X'
    uint64_t* scur;            // 440 切片目标槽表游标（原 x17）
    const char* sw_kend;       // 448 当前 sweep 的四元组结束地址 = kq + sw_len
    uint64_t* rowts;           // 456 逐行时间戳缓冲游标（-DCONV_ROWPROF，线程 0；NULL = 不记）
    const float* zi[2];        // 464/472 ZA 初值（序言装入）：jc=3 / jc=2 的 16 向量 [4t+i][16]，NULL = 无
    float* zx[2];              // 480/488 ZA 抽取（尾声存出）：jc=0 / jc=1 → 16 向量，NULL = 无
} pass_t;
// sweep 描述符：abase = 行 Y' 的平面 0 地址（含 pass 偏移）；kq = Kp[kj]；src = 累加器初值（16 向量，NULL = 0）；
// dst：kind 0 → 16 向量存回暂存区；kind 1 → 4 tile 的输出行（st4w，tile t 在 dst + 256t）
typedef struct swd { char* abase; const float* kq; const float* src; char* dst; long kind; long ntile; } swd_t;
_Static_assert(offsetof(pass_t, pon) == 80 && offsetof(pass_t, PWb) == 104 && offsetof(pass_t, sht) == 136 &&
               offsetof(pass_t, postart) == 200 && offsetof(pass_t, sdst) == 208 && offsetof(pass_t, sstr) == 240 &&
               offsetof(pass_t, PW2b) == 272 && offsetof(pass_t, PW3b) == 280 && offsetof(pass_t, poff) == 288 &&
               offsetof(pass_t, pfst) == 296 && offsetof(pass_t, jcoff) == 328 && offsetof(pass_t, sw_xc) == 336 &&
               offsetof(pass_t, sw_xk) == 344 && offsetof(pass_t, sw_len) == 360 &&
               offsetof(pass_t, inc) == 368 && offsetof(pass_t, swq) == 400 && offsetof(pass_t, sw_half) == 432 &&
               offsetof(pass_t, scur) == 440 && offsetof(pass_t, sw_kend) == 448 && offsetof(pass_t, zi) == 464 && offsetof(pass_t, zx) == 480 &&
               sizeof(swd_t) == 48 && offsetof(swd_t, ntile) == 40 &&
               offsetof(swd_t, kq) == 8 && offsetof(swd_t, src) == 16 && offsetof(swd_t, dst) == 24 && offsetof(swd_t, kind) == 32, "pass_t 布局");

// 预取游标（每次 2 线）：P = 下一线地址，E = 当前段末，N = 剩余线数；到段末则 P += jump，E += stride（跳转量从结构体取）
// 段末跳转用 csel 而不用分支：段末每 pass 只出现 4–8 次，分支预测器学不到，每次误预测都抽空 fmopa 队列
//（实测 k39/k41 −0.6%）
#define PFCUR(hint, P, E, N, OJ, OS, L)                                                                  \
    "cbz " P ", " #L "f\n\t"                                                                             \
    "prfm " hint ", [" P "]\n\t"                                                                         \
    "prfm " hint ", [" P ", #64]\n\t"                                                                    \
    "add " P ", " P ", #128\n\t"                                                                         \
    "subs " N ", " N ", #2\n\t"                                                                          \
    "csel " P ", xzr, " P ", le\n\t"          /* 线数用完：指针清零，之后 cbz 跳过 */                          \
    "ldr x9, [%[a], #" #OJ "]\n\t ldr x10, [%[a], #" #OS "]\n\t"                                          \
    "cmp " P ", " E "\n\t"                                                                               \
    "csel x9, x9, xzr, hs\n\t csel x10, x10, xzr, hs\n\t"    /* 到段末：P += jump, E += stride，否则 +0 */    \
    "add " P ", " P ", x9\n\t add " E ", " E ", x10\n\t"                                                 \
    #L ":\n\t"
// 预取/切片分散到各块组末尾（块 0/2/3：输入预取各 2 线；块 4/5：输出预取各 2 线（仅最后 postart 行）；块 1：切片），
// 避免把 ~80 条标量指令堆在同一个块组里挤占前端。KW<21 的核每行块数不足时部分槽不执行（只影响预取覆盖）。
// 预取目标层级是立即数 → 两种实例（L1 / L2 提示）运行期按 pass 长度选择：短 pass（k39/k41/k55）预取到 L1 更快；
// 长 pass（k81：每 pass 经 L1 的平面+R 数据 ~240 KB）预取进 L1 只会把热的平面/R 线挤掉，L2 提示快 0.3–0.9%。
#define EX_PFI(HI) PFCUR(HI, "x19", "x20", "x21", 48, 56, 21)
// 输出线游标：dc zva 预清零（见 read_knobs），同一游标结构；每次 2 线，因此每行线数取偶数
#define PFCUR_ZVA(P, E, N, OJ, OS, L)                                                                    \
    "cbz " P ", " #L "f\n\t"                                                                             \
    "dc zva, " P "\n\t add x9, " P ", #64\n\t dc zva, x9\n\t"                                          \
    "add " P ", " P ", #128\n\t"                                                                         \
    "subs " N ", " N ", #2\n\t"                                                                          \
    "csel " P ", xzr, " P ", le\n\t"                                                                     \
    "ldr x9, [%[a], #" #OJ "]\n\t ldr x10, [%[a], #" #OS "]\n\t"                                          \
    "cmp " P ", " E "\n\t"                                                                               \
    "csel x9, x9, xzr, hs\n\t csel x10, x10, xzr, hs\n\t"                                                \
    "add " P ", " P ", x9\n\t add " E ", " E ", x10\n\t"                                                 \
    #L ":\n\t"
// 实验（-DCONV_ZVA_CURSOR）：输出线用 dc zva 预清零代替预取。位精确，但本地 −1%（zva 要走一致性拿所有权、并发有限），
// 只在带宽饥饿（远端内存代理）时 k39 +5%/k41 +2%；默认仍是 pstl 预取（RFO 读）
#ifdef CONV_ZVA_CURSOR
#define EX_PFO(HO) "ldr x9, [%[a], #200]\n\t cmp x14, x9\n\t b.hi 29f\n\t" PFCUR_ZVA("x24", "x25", "x26", 88, 96, 23) "29:\n\t"
#else
#define EX_PFO(HO) "ldr x9, [%[a], #200]\n\t cmp x14, x9\n\t b.hi 29f\n\t" PFCUR(HO, "x24", "x25", "x26", 88, 96, 23) "29:\n\t"
#endif
// 回写重叠：剩余行数 x14 ∈ {3,2,1} 的行内，把 tile T 已完成的输出行 jc = x14（竖切片 c = jc, jc+4, jc+8, jc+12，
// 即 ic = 0..3）用 mova 取出并 st4w 交织成 64 个连续 float；目标 = sdst[T] + (3-jc)*sstr[T]；sdst[T]=0 则跳过。
// 放在块 6..9（每块一个 tile），要求每行至少 10 个块组（m4 ≥ 10，即 KW ≥ 37），否则由 C 回写全部四行。
// 另外在 x14 = 4..1 的行里把该 tile 下一步要写的输出行（j0 + 4 - x14）的 4 线预取进 L1：早先的 pstl 预取（postart 行前）
// 只保证线在 L2，到回写时早被平面/R 数据挤出 L1，st4w 就要等 RFO。
// 回写行 jc' = x14 + jcoff（经典 jcoff=0；边界行方案的 Y 循环少跑 jcoff 个尾行）；jc'=4 只预取 j0 行
// 4 路交织 + 非时序存储：与 st4w {Z0-Z3} 等价（out[4r+k] = Zk[r]），8 条 zip 用 3 个临时寄存器，Z0..Z3 被破坏。
// 输出线只写一次、再不读，stnt1w 让它不占 L2 也不触发 RFO 读（整线顺序写走写流模式）
#define ZIP4_STNT(Z0, Z1, Z2, Z3, T0, T1, T2, X) \
    "zip1 z" #T0 ".s, z" #Z0 ".s, z" #Z2 ".s\n\t zip2 z" #T1 ".s, z" #Z0 ".s, z" #Z2 ".s\n\t" \
    "zip1 z" #Z0 ".s, z" #Z1 ".s, z" #Z3 ".s\n\t zip2 z" #T2 ".s, z" #Z1 ".s, z" #Z3 ".s\n\t" \
    "zip1 z" #Z1 ".s, z" #T0 ".s, z" #Z0 ".s\n\t zip2 z" #Z3 ".s, z" #T0 ".s, z" #Z0 ".s\n\t" \
    "zip1 z" #T0 ".s, z" #T1 ".s, z" #T2 ".s\n\t zip2 z" #Z0 ".s, z" #T1 ".s, z" #T2 ".s\n\t" \
    "stnt1w {z" #Z1 ".s}, p0, [" X "]\n\t stnt1w {z" #Z3 ".s}, p0, [" X ", #1, mul vl]\n\t" \
    "stnt1w {z" #T0 ".s}, p0, [" X ", #2, mul vl]\n\t stnt1w {z" #Z0 ".s}, p0, [" X ", #3, mul vl]\n\t"
#ifdef CONV_NTSTORE   // 实验：非时序流式回写（不预取时本地 −1.3..−4.2%，远端内存 +2..+6%）
#define OUT_ST4(Z0, Z1, Z2, Z3, X) ZIP4_STNT(Z0, Z1, Z2, Z3, 3, 4, 15, X)
#else
#define OUT_ST4(Z0, Z1, Z2, Z3, X) "st4w {z" #Z0 ".s-z" #Z3 ".s}, p0, [" X "]\n\t"
#endif
#define EX_STORE(T, L, L2)                                                                               \
    "ldr x11, [%[a], #328]\n\t add x9, x14, x11\n\t"                                                     \
    "cmp x9, #4\n\t b.hi " #L "f\n\t"                                                                     \
    "ldr x10, [%[a], #" #T "*8+240]\n\t"                                                                 \
    "ldr x11, [%[a], #" #T "*8+296]\n\t cbz x11, " #L2 "f\n\t"                                           \
    "msub x11, x9, x10, x11\n\t add x11, x11, x10, lsl #2\n\t"          /* base + (4-jc')*stride */        \
    "prfm pstl1keep, [x11]\n\t prfm pstl1keep, [x11, #64]\n\t prfm pstl1keep, [x11, #128]\n\t prfm pstl1keep, [x11, #192]\n\t" \
    #L2 ":\n\t"                                                                                          \
    "cmp x9, #3\n\t b.hi " #L "f\n\t"                                                                     \
    "ldr x11, [%[a], #" #T "*8+208]\n\t cbz x11, " #L "f\n\t"                                            \
    "msub x11, x9, x10, x11\n\t add x11, x11, x10\n\t add x11, x11, x10, lsl #1\n\t"   /* base + (3-jc')*stride */ \
    "ldr x10, [%[a], #328]\n\t add w14, w14, w10\n\t"                    /* 切片索引寄存器只能用 w12..w15：借 w14 */ \
    "mova z14.s, p0/m, za" #T "v.s[w14, 0]\n\t add w14, w14, #4\n\t"                                     \
    "mova z13.s, p0/m, za" #T "v.s[w14, 0]\n\t add w14, w14, #4\n\t"                                     \
    "mova z12.s, p0/m, za" #T "v.s[w14, 0]\n\t add w14, w14, #4\n\t"                                     \
    "mova z11.s, p0/m, za" #T "v.s[w14, 0]\n\t sub w14, w14, #12\n\t sub w14, w14, w10\n\t"              \
    OUT_ST4(11, 12, 13, 14, "x11")                                                                       \
    #L ":\n\t"

// 边界行 fmla 步（每个块组末尾）：有活动 sweep 时走一步 X'；sweep 结束时把 16 个累加器存出（暂存区或输出行），
// 取下一个描述符并装入其初值（NULL → 清零）。累加器 z16+4t+i 对应 tile t、ic = 3-i（与 st4w 的列序一致）。
#define FML4(A, R0, R1, R2, R3) \
    "fmla z" #R0 ".s, z" #A ".s, z0.s[3]\n\t fmla z" #R1 ".s, z" #A ".s, z0.s[2]\n\t" \
    "fmla z" #R2 ".s, z" #A ".s, z0.s[1]\n\t fmla z" #R3 ".s, z" #A ".s, z0.s[0]\n\t"
#define ST8(X, R0, R1, R2, R3, R4, R5, R6, R7) \
    "st1w {z" #R0 ".s}, p0, [" X "]\n\t st1w {z" #R1 ".s}, p0, [" X ", #1, mul vl]\n\t st1w {z" #R2 ".s}, p0, [" X ", #2, mul vl]\n\t st1w {z" #R3 ".s}, p0, [" X ", #3, mul vl]\n\t" \
    "st1w {z" #R4 ".s}, p0, [" X ", #4, mul vl]\n\t st1w {z" #R5 ".s}, p0, [" X ", #5, mul vl]\n\t st1w {z" #R6 ".s}, p0, [" X ", #6, mul vl]\n\t st1w {z" #R7 ".s}, p0, [" X ", #7, mul vl]\n\t"
#define LD8(X, R0, R1, R2, R3, R4, R5, R6, R7) \
    "ld1w {z" #R0 ".s}, p0/z, [" X "]\n\t ld1w {z" #R1 ".s}, p0/z, [" X ", #1, mul vl]\n\t ld1w {z" #R2 ".s}, p0/z, [" X ", #2, mul vl]\n\t ld1w {z" #R3 ".s}, p0/z, [" X ", #3, mul vl]\n\t" \
    "ld1w {z" #R4 ".s}, p0/z, [" X ", #4, mul vl]\n\t ld1w {z" #R5 ".s}, p0/z, [" X ", #5, mul vl]\n\t ld1w {z" #R6 ".s}, p0/z, [" X ", #6, mul vl]\n\t ld1w {z" #R7 ".s}, p0/z, [" X ", #7, mul vl]\n\t"
// sweep 状态寄存器：x15 = 当前 a 地址（0 = 无活动 sweep），x17 = 当前 kernel 四元组地址（bit0 = 半步标志）；
// 结束地址在 pass_t.sw_kend。装入当前描述符（x9）的累加器初值：src 为 NULL 则清零，为 1 则沿用（链式）
#define SW_LOAD \
    "ldr x11, [x9, #16]\n\t cbz x11, 83f\n\t cmp x11, #1\n\t b.eq 85f\n\t"   /* src=1：链式衔接，累加器沿用 */ \
    LD8("x11", 16, 17, 18, 19, 20, 21, 22, 23) "add x11, x11, #512\n\t" LD8("x11", 24, 25, 26, 27, 28, 29, 30, 31) "b 85f\n\t" \
    "83:\n\t mov z16.s, #0\n\t mov z17.s, #0\n\t mov z18.s, #0\n\t mov z19.s, #0\n\t mov z20.s, #0\n\t mov z21.s, #0\n\t mov z22.s, #0\n\t mov z23.s, #0\n\t" \
    "mov z24.s, #0\n\t mov z25.s, #0\n\t mov z26.s, #0\n\t mov z27.s, #0\n\t mov z28.s, #0\n\t mov z29.s, #0\n\t mov z30.s, #0\n\t mov z31.s, #0\n\t"
// 每个 sweep 首次触碰 ~30 条线（4 平面 × 4 tile × 2 线）是 L2 命中，集中在 sweep 的前 4 个 X'。任何形式的软件预取
//（一次性 30 条 / 上一 sweep 末尾每半步 6 条 / 前 32 个 X' 每步 1 条）都更慢 0.3–5%：半步周围的瓶颈是指令发射带宽，
// 不是 L2 延迟——多 1 条 prfm + 十几条标量就把 k39 拖慢 5%。所以半步只保留必需指令。
// 取下一个描述符（x9 = 当前描述符）：x15/x17 ← abase/kq，sw_kend ← kq + 4(KW+3)，装入初值；abase=0 → x15=0 结束。
// 半步标志放在 x17 的 bit0（kq 地址 4 B 对齐）：0 → 下一半步做 tile 0/1，1 → tile 2/3
#define SW_NEXT \
    "add x9, x9, #48\n\t str x9, [%[a], #400]\n\t ldr x15, [x9]\n\t cbz x15, 85f\n\t" \
    "ldr x17, [x9, #8]\n\t ldr x11, [%[a], #360]\n\t add x11, x17, x11\n\t str x11, [%[a], #448]\n\t" \
    SW_LOAD
// 半步：half 0 → tile 0/1（载 kernel 四元组），half 1 → tile 2/3，然后推进 X'；X' 用完 → 存累加器、取下一个描述符
#define SW_LD0 "ld1w {z1.s}, p0/z, [x15]\n\t ld1w {z2.s}, p0/z, [x15, #1, mul vl]\n\t ld1rqw {z0.s}, p0/z, [x17]\n\t"
#define SW_LD1 "ld1w {z1.s}, p0/z, [x15, #2, mul vl]\n\t ld1w {z2.s}, p0/z, [x15, #3, mul vl]\n\t"
#define EX_HALF \
    "cbz x15, 85f\n\t" \
    "tbnz x17, #0, 84f\n\t" \
    SW_LD0 \
    "orr x17, x17, #1\n\t" \
    FML4(1, 16, 17, 18, 19) FML4(2, 20, 21, 22, 23) "b 85f\n\t" \
    "84:\n\t bic x17, x17, #1\n\t" \
    SW_LD1 \
    FML4(1, 24, 25, 26, 27) FML4(2, 28, 29, 30, 31) \
    "and x11, x17, #12\n\t add x11, %[a], x11, lsl #1\n\t ldr x11, [x11, #368]\n\t add x15, x15, x11\n\t"  /* a 地址按 X' mod 4 推进 */ \
    "add x17, x17, #4\n\t ldr x11, [%[a], #448]\n\t cmp x17, x11\n\t b.lo 85f\n\t"                          /* 四元组滑一个元素 */ \
    /* sweep 结束：存累加器 */ \
    "ldr x9, [%[a], #400]\n\t ldr x10, [x9, #24]\n\t ldr x11, [x9, #32]\n\t cbz x11, 81f\n\t cmp x11, #2\n\t b.eq 82f\n\t" \
    "ldr x11, [x9, #40]\n\t"                                                   /* 只存前 ntile 个 tile */ \
    OUT_ST4(16, 17, 18, 19, "x10") "add x10, x10, #256\n\t cmp x11, #2\n\t b.lo 82f\n\t" \
    OUT_ST4(20, 21, 22, 23, "x10") "add x10, x10, #256\n\t cmp x11, #3\n\t b.lo 82f\n\t" \
    OUT_ST4(24, 25, 26, 27, "x10") "add x10, x10, #256\n\t cmp x11, #4\n\t b.lo 82f\n\t" \
    OUT_ST4(28, 29, 30, 31, "x10") "b 82f\n\t" \
    "81:\n\t" ST8("x10", 16, 17, 18, 19, 20, 21, 22, 23) "add x10, x10, #512\n\t" ST8("x10", 24, 25, 26, 27, 28, 29, 30, 31) \
    "82:\n\t" SW_NEXT \
    "85:\n\t"
#define EX_NONE
// 各块组末尾的附加工作：块 0 输入预取、块 1 切片、块 2/3 输入预取 + tile 0/1 回写、块 4/5 输出预取 + tile 2/3 回写
//（回写放在块 6..9 时 k39（每行恰 10 块）末块紧接行尾，实测不如并入块 2..5）
#define EXB2(HI, HO) EX_PFI(HI) EX_STORE(0, 51, 61)
#define EXB3(HI, HO) EX_PFI(HI) EX_STORE(1, 52, 62)
#define EXB4(HI, HO) EX_PFO(HO) EX_STORE(2, 53, 63)
#define EXB5(HI, HO) EX_PFO(HO) EX_STORE(3, 54, 64)
#define STORE_MIN_M4 6
//（试过在块 7..9 把下一行的平面/R 行预取进 L1：k39 反而慢 2.5%，这些线本来就由硬件预取/顺序访问覆盖，多余 prfm 只挤载入口）

// 切片构建（每个 16 块组执行一次，放在块 0 之后）：把下一组一个新行的 64 列用 ld4w 去交织进 4 个平面，
// x22 = src，x23 = dst（平面 0），x27 = 本行剩余片数，x28 = 剩余行数（含哑行），x17 = 目标槽表游标。
// 只用载入/存储管线（ld4w 8 周期，占用本步组的载入空闲），不用向量置换管线（uzp 会与 ext/fmopa 争端口）。
#define SLICE_ROW                                                                                        \
    "cbz x28, 41f\n\t"                                                                                   \
    "ld4w {z11.s-z14.s}, p0/z, [x22]\n\t"                                                                \
    "ldr x9, [%[a], #104]\n\t add x10, x23, x9\n\t add x11, x10, x9\n\t add x9, x11, x9\n\t"            \
    "st1w {z11.s}, p0, [x23]\n\t st1w {z12.s}, p0, [x10]\n\t st1w {z13.s}, p0, [x11]\n\t st1w {z14.s}, p0, [x9]\n\t" \
    "add x22, x22, #256\n\t add x23, x23, #64\n\t"                                                      \
    "subs x27, x27, #1\n\t b.ne 41f\n\t"                                                                \
    "ldr x9, [%[a], #176]\n\t add x22, x22, x9\n\t"          /* 下一行 src */                              \
    "ldr x9, [%[a], #440]\n\t ldr x23, [x9], #8\n\t str x9, [%[a], #440]\n\t"   /* 下一行目标槽（游标在内存） */ \
    "ldr x27, [%[a], #160]\n\t"                                                                          \
    "sub x28, x28, #1\n\t"                                                                               \
    "41:\n\t"

// ZA 初值装入 / 抽取（pass 序言 / 尾声，直线代码；此前是 C 里 8 个独立 asm 块，每 pass 多 ~100 周期）：
// 16 向量布局 [4t+i][16]，tile t 的 4 个竖切片 c = w12..w15（i=0 ↔ w12），x9 = 基址
#define ZI_TILE(T, X) "ld1w {z0.s}, p0/z, [" X "]\n\t ld1w {z1.s}, p0/z, [" X ", #1, mul vl]\n\t ld1w {z2.s}, p0/z, [" X ", #2, mul vl]\n\t ld1w {z3.s}, p0/z, [" X ", #3, mul vl]\n\t" \
    "mova za" #T "v.s[w12, 0], p0/m, z0.s\n\t mova za" #T "v.s[w13, 0], p0/m, z1.s\n\t mova za" #T "v.s[w14, 0], p0/m, z2.s\n\t mova za" #T "v.s[w15, 0], p0/m, z3.s\n\t"
#define ZX_TILE(T, X) "mova z0.s, p0/m, za" #T "v.s[w12, 0]\n\t mova z1.s, p0/m, za" #T "v.s[w13, 0]\n\t mova z2.s, p0/m, za" #T "v.s[w14, 0]\n\t mova z3.s, p0/m, za" #T "v.s[w15, 0]\n\t" \
    "st1w {z0.s}, p0, [" X "]\n\t st1w {z1.s}, p0, [" X ", #1, mul vl]\n\t st1w {z2.s}, p0, [" X ", #2, mul vl]\n\t st1w {z3.s}, p0, [" X ", #3, mul vl]\n\t"
#define ZA_ROW(MACRO, JC, OFF, L) \
    "ldr x9, [%[a], #" #OFF "]\n\t cbz x9, " #L "f\n\t" \
    "mov w12, #" #JC "+12\n\t mov w13, #" #JC "+8\n\t mov w14, #" #JC "+4\n\t mov w15, #" #JC "\n\t" \
    "add x10, x9, #256\n\t add x11, x9, #512\n\t add x16, x9, #768\n\t" \
    MACRO(0, "x9") MACRO(1, "x10") MACRO(2, "x11") MACRO(3, "x16") \
    #L ":\n\t"
#ifdef CONV_ROWPROF   // 剖析：每行行首记一次 cntvct（线程 0），事后按行号统计每行时长
#define ROWTS "ldr x10, [%[a], #456]\n\t cbz x10, 11f\n\t mrs x9, cntvct_el0\n\t str x9, [x10], #8\n\t str x10, [%[a], #456]\n\t 11:\n\t"
#else
#define ROWTS
#endif
// 行首软流水：本行平面 0 基址已在 x16（上一行末/序言算好：槽表项 + pass 偏移），行首只需 mov，随后立刻取下一行的项。
// 行首链 ldr→add→ld1w→ext→fmopa 会抽空 SME 队列：去掉链头的 ldr 后 k39 +1.4%（v29 的"预载"仍留着 ldr+add 在链上，所以无效）
#define ROW_P0 "mov %[p0], x16\n\t ldr x16, [x12], #8\n\t ldr x9, [%[a], #288]\n\t add x16, x16, x9\n\t"
#define ROW_P0_INIT "ldr x16, [x12], #8\n\t ldr x9, [%[a], #288]\n\t add x16, x16, x9\n\t"
#define PASS_LOOP(STEP, TAIL, HI, HO)                                                                       \
    asm volatile("ptrue p0.s\n\t zero {za}\n\t"                                                             \
                 ZA_ROW(ZI_TILE, 3, 464, 60) ZA_ROW(ZI_TILE, 2, 472, 61)                                    \
                 "ldr x12, [%[a], #0]\n\t ldr x13, [%[a], #8]\n\t ldr x14, [%[a], #16]\n\t"                 \
                 "ldr x19, [%[a], #24]\n\t ldr x20, [%[a], #32]\n\t ldr x21, [%[a], #40]\n\t"               \
                 "ldr x24, [%[a], #64]\n\t ldr x25, [%[a], #72]\n\t ldr x26, [%[a], #80]\n\t"               \
                 "ldr x22, [%[a], #144]\n\t ldr x9, [%[a], #152]\n\t str x9, [%[a], #440]\n\t ldr x23, [%[a], #184]\n\t" \
                 "ldr x27, [%[a], #192]\n\t ldr x28, [%[a], #168]\n\t"   /* 哑行：sdcnt 片写到 sdummy */        \
                 "cbnz x21, 32f\n\t mov x19, xzr\n\t 32:\n\t"          /* 无预取任务：指针清零 */                \
                 "cbnz x26, 33f\n\t mov x24, xzr\n\t 33:\n\t"                                               \
                 "ldr x15, [%[a], #336]\n\t ldr x17, [%[a], #344]\n\t"  /* sweep 状态；首个 sweep 的初值 */      \
                 "cbz x15, 85f\n\t ldr x9, [%[a], #400]\n\t" SW_LOAD "85:\n\t"                        \
                 ROW_P0_INIT                                                                                \
                 "10:\n\t"                                                                                  \
                 ROWTS                                                                                      \
                 /* 行首：平面基址 = 槽表项 + pass 偏移；PWb/2PWb/3PWb 互不依赖 */                                 \
                 ROW_P0                                                                                     \
                 "ldr x9, [%[a], #104]\n\t ldr x10, [%[a], #272]\n\t ldr x11, [%[a], #280]\n\t"             \
                 "add %[p1], %[p0], x9\n\t add %[p2], %[p0], x10\n\t add %[p3], %[p0], x11\n\t"             \
                 "mov %[pb], x13\n\t ldr x9, [%[a], #112]\n\t add x13, x13, x9\n\t"                          \
                 "ldr %[m], [%[a], #120]\n\t"                                                               \
                 "cbz %[m], 9f\n\t"                                                                         \
                 "1:\n\t"                                                                                   \
                 BLOCKX_A(0, STEP, EX_PFI(HI)) BLOCKX_B(4, STEP, SLICE_ROW) BLOCKX_C(8, STEP, EXB2(HI, HO)) BLOCKX_A(12, STEP, EXB3(HI, HO)) \
                 BLOCKX_B(16, STEP, EXB4(HI, HO)) BLOCKX_C(20, STEP, EXB5(HI, HO)) BLOCKX_A(24, STEP, EX_NONE) BLOCKX_B(28, STEP, EX_NONE) \
                 BLOCKX_C(32, STEP, EX_NONE) BLOCKX_A(36, STEP, EX_NONE) BLOCKX_B(40, STEP, EX_NONE) BLOCKX_C(44, STEP, EX_NONE) \
                 BLOCKX_A(48, STEP, EX_NONE) BLOCKX_B(52, STEP, EX_NONE) BLOCKX_C(56, STEP, EX_NONE) BLOCKX_A(60, STEP, EX_NONE) \
                 "add %[p0], %[p0], #64\n\t add %[p1], %[p1], #64\n\t add %[p2], %[p2], #64\n\t add %[p3], %[p3], #64\n\t" \
                 "b 1b\n\t"                                                                                 \
                 "9:\n\t"                                                                                   \
                 "ldr x9, [%[a], #136]\n\t"                                                                 \
                 "add x10, %[p1], x9\n\t add x11, %[p2], x9\n\t add x9, %[p0], x9\n\t"                      \
                 "ldr %[m], [%[a], #128]\n\t"                                                               \
                 "cmp %[m], #1\n\t b.lt 8f\n\t" TAIL(x9)                                                    \
                 "cmp %[m], #2\n\t b.lt 8f\n\t" TAIL(x10)                                                   \
                 "cmp %[m], #3\n\t b.lt 8f\n\t" TAIL(x11)                                                   \
                 "8:\n\t"                                                                                   \
                 "subs x14, x14, #1\n\t b.ne 10b\n\t"                                                       \
                 /* 队列未走完（步数预算留了 10% 余量，正常不会）：在此排空，保证累加器不跨 asm 存活 */                \
                 "76:\n\t cbz x15, 77f\n\t" EX_HALF "b 76b\n\t 77:\n\t"                                     \
                 "str x15, [%[a], #336]\n\t str x17, [%[a], #344]\n\t"                                       \
                 ZA_ROW(ZX_TILE, 0, 480, 62) ZA_ROW(ZX_TILE, 1, 488, 63)                                    \
                 : [p0] "=&r"(p0), [p1] "=&r"(p1), [p2] "=&r"(p2), [p3] "=&r"(p3), [pb] "=&r"(pb), [m] "=&r"(m) \
                 : [a] "r"(a)                                                                               \
                 : "memory", "cc", VCLOB, "p0", "x9", "x10", "x11", "x12", "x13", "x14", "x15", "x16", "x17", \
                   "x19", "x20", "x21", "x22", "x23", "x24", "x25", "x26", "x27", "x28")

// 单独排空 sweep 队列（范围起点的"前半"、范围终点的"后半"没有可重叠的 pass）
static void sweep_drain(pass_t* a)
{
    a->sw_dense = 1;
    asm volatile("ptrue p0.s\n\t"
                 "ldr x15, [%[a], #336]\n\t ldr x17, [%[a], #344]\n\t cbz x15, 89f\n\t ldr x9, [%[a], #400]\n\t" SW_LOAD "85:\n\t"
                 "88:\n\t cbz x15, 89f\n\t" EX_HALF "b 88b\n\t 89:\n\t str x15, [%[a], #336]\n\t"
                 : : [a] "r"(a) : "memory", "cc", VCLOB, "p0", "x9", "x10", "x11", "x15", "x17");
}

#ifdef CONV_DEBUG_BR
// 合成数据的单 sweep 自检：plane_q[x] = 1000q + x（4 平面，PW=80），Kp = [0,0,0,1,2,..,9,0,...]，len 12
static void br_selftest(void)
{
    static float planes[4 * 80] __attribute__((aligned(256)));
    static float kp[16] __attribute__((aligned(64)));
    static float acc[16][16] __attribute__((aligned(64)));
    static swd_t q[2] __attribute__((aligned(64)));
    for (int qq = 0; qq < 4; qq++) for (int x = 0; x < 80; x++) planes[qq * 80 + x] = 1000.0f * qq + x;
    for (int z = 0; z < 16; z++) kp[z] = (z >= 3 && z < 12) ? (float)(z - 2) : 0.0f;    // k[ki] = ki+1
    for (int L = 1; L <= 12; L += (L < 4 ? 1 : 8)) {
        pass_t pa; memset(&pa, 0, sizeof(pa));
        pa.PWb = 320; pa.sw_len = 4 * L; pa.inc[0] = pa.inc[1] = pa.inc[2] = 320; pa.inc[3] = -3 * 320 + 4;
        q[0].abase = (char*)planes; q[0].kq = kp; q[0].src = NULL; q[0].dst = (char*)acc; q[0].kind = 0; q[0].ntile = 4; q[1].abase = NULL;
        pa.swq = q; pa.sw_xc = q[0].abase; pa.sw_xk = (const char*)q[0].kq; pa.sw_kend = pa.sw_xk + pa.sw_len; pa.sw_half = 0;
        memset(acc, 0, sizeof(acc));
        asm volatile("smstart\n\t" ::: "memory", VCLOB, PCLOB);
        sweep_drain(&pa);
        asm volatile("smstop\n\t" ::: "memory", VCLOB, PCLOB);
        // 参考：acc[t][i][r] = Σ_{X'} a_t(X')[r] * kp[X'+ic]，a_t(X')[r] = planes[(X'%4)*80 + X'/4 + 16t + r]，ic = 3-i
        for (int t = 0; t < 2; t++) for (int i = 0; i < 4; i++) {
            float ref[2] = {0, 0};
            for (int X = 0; X < L; X++) for (int r = 0; r < 2; r++) ref[r] = __builtin_fmaf(planes[(X % 4) * 80 + X / 4 + 16 * t + r], kp[X + 3 - i], ref[r]);
            fprintf(stderr, "  selftest len %2d t%d i%d: got %.1f %.1f  ref %.1f %.1f\n", L, t, i, acc[4 * t + i][0], acc[4 * t + i][1], ref[0], ref[1]);
        }
        fprintf(stderr, "  selftest state: xc %p swq %p\n", (void*)pa.sw_xc, (void*)pa.swq);
    }
}
#endif

// nt = 活跃 tile 数；l2 = DRAM 预取到 L2（否则 L1）
static void pass_steps(int nt, pass_t* a, int l2)
{
    const float *p0, *p1, *p2, *p3, *pb;
    long m;
    if (l2) {
        switch (nt) {
        case 4: PASS_LOOP(STEP4X, TAIL4, "pldl2keep", "pstl2keep"); break;
        case 3: PASS_LOOP(STEP3X, TAIL3, "pldl2keep", "pstl2keep"); break;
        case 2: PASS_LOOP(STEP2X, TAIL2, "pldl2keep", "pstl2keep"); break;
        default: PASS_LOOP(STEP1X, TAIL1, "pldl2keep", "pstl2keep"); break;
        }
    } else {
        switch (nt) {
        case 4: PASS_LOOP(STEP4X, TAIL4, "pldl1keep", "pstl1keep"); break;
        case 3: PASS_LOOP(STEP3X, TAIL3, "pldl1keep", "pstl1keep"); break;
        case 2: PASS_LOOP(STEP2X, TAIL2, "pldl1keep", "pstl1keep"); break;
        default: PASS_LOOP(STEP1X, TAIL1, "pldl1keep", "pstl1keep"); break;
        }
    }
    (void)p0; (void)p1; (void)p2; (void)p3; (void)pb; (void)m;
}

// 把 tile T 的输出行 jc（4 个竖切片 c=12+jc, 8+jc, 4+jc, jc）交织后存到 dst（64 个连续 float）
#define STORE_TILE_ROW(T)                                                                   \
    asm volatile("ptrue p0.s\n\t"                                                           \
                 "add w12, %w[jc], #12\n\t"                                                 \
                 "add w13, %w[jc], #8\n\t"                                                  \
                 "add w14, %w[jc], #4\n\t"                                                  \
                 "mov w15, %w[jc]\n\t"                                                      \
                 "mova z0.s, p0/m, za" #T "v.s[w12, 0]\n\t"                                 \
                 "mova z1.s, p0/m, za" #T "v.s[w13, 0]\n\t"                                 \
                 "mova z2.s, p0/m, za" #T "v.s[w14, 0]\n\t"                                 \
                 "mova z3.s, p0/m, za" #T "v.s[w15, 0]\n\t"                                 \
                 "st4w {z0.s-z3.s}, p0, [%[d]]\n\t"                                        \
                 : : [jc] "r"(jc), [d] "r"(dst) : "memory", "x12", "x13", "x14", "x15", "z0", "z1", "z2", "z3", "p0")

static inline void store_tile_row(int t, int jc, float* dst)
{
    switch (t) {
    case 0: STORE_TILE_ROW(0); break;
    case 1: STORE_TILE_ROW(1); break;
    case 2: STORE_TILE_ROW(2); break;
    default: STORE_TILE_ROW(3); break;
    }
}
// 同上，但落到输出行时用非时序存储（临时 z4..z6）
#define STORE_TILE_ROW_NT(T)                                                                \
    asm volatile("ptrue p0.s\n\t"                                                           \
                 "add w12, %w[jc], #12\n\t add w13, %w[jc], #8\n\t add w14, %w[jc], #4\n\t mov w15, %w[jc]\n\t" \
                 "mova z0.s, p0/m, za" #T "v.s[w12, 0]\n\t mova z1.s, p0/m, za" #T "v.s[w13, 0]\n\t" \
                 "mova z2.s, p0/m, za" #T "v.s[w14, 0]\n\t mova z3.s, p0/m, za" #T "v.s[w15, 0]\n\t" \
                 ZIP4_STNT(0, 1, 2, 3, 4, 5, 6, "%[d]")                                     \
                 : : [jc] "r"(jc), [d] "r"(dst) : "memory", "x12", "x13", "x14", "x15", "z0", "z1", "z2", "z3", "z4", "z5", "z6", "p0")
static inline void store_tile_row_out(int t, int jc, float* dst)
{
#ifndef CONV_NTSTORE
    store_tile_row(t, jc, dst);
#else
    switch (t) {
    case 0: STORE_TILE_ROW_NT(0); break;
    case 1: STORE_TILE_ROW_NT(1); break;
    case 2: STORE_TILE_ROW_NT(2); break;
    default: STORE_TILE_ROW_NT(3); break;
    }
#endif
}

// 去交织一行输入到 4 个平面：plane_q[x] = in[row][i0 + 4x + q]（x < PW；越界补 0）
// 两种实现：ld4w（一条指令 256 B，串行化，行在 L2 时每条 ~40 周期）；ld1w×4 + uzp×8（载入相互独立，可并发发出）
static int g_build_uzp = 1;
static inline void build_planes(const float* src, long ncols, long PW, float* P)
{
    // ncols：从 i0 起该行剩余的列数（<=0 或行越界时 src=NULL → 全零）
    svbool_t all = svptrue_b32();
    long xfull = src ? (ncols > 0 ? ncols / 4 : 0) : 0;
    long x = 0;
    if (g_build_uzp && src) {
        // 整块：x+16 <= xfull（64 个输入元素全部有效）；一次两块，8 条独立载入先发出（行在 L2，靠 MLP 遮延迟）
        for (; x + 32 <= xfull && x + 32 <= PW; x += 32) {
            const float* q = src + 4 * x;
            svfloat32_t v0 = svld1_f32(all, q), v1 = svld1_f32(all, q + 16), v2 = svld1_f32(all, q + 32), v3 = svld1_f32(all, q + 48);
            svfloat32_t w0 = svld1_f32(all, q + 64), w1 = svld1_f32(all, q + 80), w2 = svld1_f32(all, q + 96), w3 = svld1_f32(all, q + 112);
            svfloat32_t e0 = svuzp1_f32(v0, v1), o0 = svuzp2_f32(v0, v1), e1 = svuzp1_f32(v2, v3), o1 = svuzp2_f32(v2, v3);
            svfloat32_t f0 = svuzp1_f32(w0, w1), g0 = svuzp2_f32(w0, w1), f1 = svuzp1_f32(w2, w3), g1 = svuzp2_f32(w2, w3);
            svst1_f32(all, P + x, svuzp1_f32(e0, e1));
            svst1_f32(all, P + 2 * PW + x, svuzp2_f32(e0, e1));
            svst1_f32(all, P + PW + x, svuzp1_f32(o0, o1));
            svst1_f32(all, P + 3 * PW + x, svuzp2_f32(o0, o1));
            svst1_f32(all, P + x + 16, svuzp1_f32(f0, f1));
            svst1_f32(all, P + 2 * PW + x + 16, svuzp2_f32(f0, f1));
            svst1_f32(all, P + PW + x + 16, svuzp1_f32(g0, g1));
            svst1_f32(all, P + 3 * PW + x + 16, svuzp2_f32(g0, g1));
        }
        for (; x + 16 <= xfull && x < PW; x += 16) {
            const float* q = src + 4 * x;
            svfloat32_t v0 = svld1_f32(all, q), v1 = svld1_f32(all, q + 16), v2 = svld1_f32(all, q + 32), v3 = svld1_f32(all, q + 48);
            svfloat32_t e0 = svuzp1_f32(v0, v1), o0 = svuzp2_f32(v0, v1), e1 = svuzp1_f32(v2, v3), o1 = svuzp2_f32(v2, v3);
            svst1_f32(all, P + x, svuzp1_f32(e0, e1));            // 列 ≡ 0 (mod 4)
            svst1_f32(all, P + 2 * PW + x, svuzp2_f32(e0, e1));   // ≡ 2
            svst1_f32(all, P + PW + x, svuzp1_f32(o0, o1));       // ≡ 1
            svst1_f32(all, P + 3 * PW + x, svuzp2_f32(o0, o1));   // ≡ 3
        }
    }
    for (; x < PW; x += 16) {
        svbool_t pg = svwhilelt_b32((int64_t)x, (int64_t)xfull);
        svfloat32x4_t v = svld4_f32(pg, src ? src + 4 * x : (const float*)P);
        svst1_f32(all, P + x, svget4_f32(v, 0));
        svst1_f32(all, P + PW + x, svget4_f32(v, 1));
        svst1_f32(all, P + 2 * PW + x, svget4_f32(v, 2));
        svst1_f32(all, P + 3 * PW + x, svget4_f32(v, 3));
    }
    if (src && xfull < PW) {
        long r = ncols - 4 * xfull;   // 0..3 个尾元素
        for (long q = 0; q < r && q < 4; q++) P[q * PW + xfull] = src[4 * xfull + q];
    }
}

// 构建一个 16 元素切片：plane_q[x0..x0+16) ← in[row][i0 + 4x .. )（含边界/越界补零）
static inline void build_slice(const float* src, long ncols, long PW, float* P, long x0)
{
    svbool_t all = svptrue_b32();
    long xfull = ncols > 0 ? ncols / 4 : 0;
    svbool_t pg = svwhilelt_b32((int64_t)x0, (int64_t)xfull);
    svfloat32x4_t v = svld4_f32(pg, src + 4 * x0);
    svst1_f32(all, P + x0, svget4_f32(v, 0));
    svst1_f32(all, P + PW + x0, svget4_f32(v, 1));
    svst1_f32(all, P + 2 * PW + x0, svget4_f32(v, 2));
    svst1_f32(all, P + 3 * PW + x0, svget4_f32(v, 3));
    if (xfull >= x0 && xfull < x0 + 16) {
        long r = ncols - 4 * xfull;
        for (long q = 0; q < r && q < 4; q++) P[q * PW + xfull] = src[4 * xfull + q];
    }
}

// ---------------------------------------------------------------- 缓冲
static float* g_R = NULL;
static size_t g_Rcap = 0;
static float* g_Kp = NULL;          // 边界行 fmla 用的零填充 kernel 行：Kp[kj][z] = k[kj][z-3]（z∈[3,KW+3)），行距 KPS
static size_t g_Kpcap = 0;
typedef struct { uint64_t w; char pad[56]; } work_t;
static work_t g_work[1024] __attribute__((aligned(64)));
typedef struct { uint64_t v; char pad[56]; } padded_u64;
static padded_u64 g_rcount __attribute__((aligned(64)));    // R 打包完成计数（每次调用前清零，到 nt 即全部完成）
static uint64_t g_call = 0;
static float* g_P = NULL;
static size_t g_Pcap = 0;
static uint64_t* g_tab = NULL;      // 每线程槽表（2NS+1 项环形展开）
static size_t g_tab_cap = 0, g_tab_stride = 0;

// 2 MB 对齐 + 整数个 2 MB + MADV_HUGEPAGE：让环形缓冲、打包 kernel、槽表落在透明大页上（节点 THP=always），
// 否则 k81 的 R（84 行 × 2 KB = 42 个 4 KB 页）+ 环形缓冲每 pass 轮转的页数会压迫一级 DTLB
#include <sys/mman.h>
static void* alloc_aligned(size_t bytes)
{
    void* p = NULL;
    const size_t HP = 2u << 20;
    size_t sz = (bytes + HP - 1) & ~(HP - 1);
    if (posix_memalign(&p, HP, sz) != 0) return NULL;
#ifdef MADV_HUGEPAGE
    madvise(p, sz, MADV_HUGEPAGE);
#endif
    return p;
}

// ≥ bytes 的最小 2 的幂（≤ 4096），超过 4 KB 时向上取整到 4 KB 的倍数
static long pow2_stride(long bytes)
{
    long s = 64;
    while (s < bytes && s < 4096) s <<= 1;
    if (s < bytes) s = (bytes + 4095) & ~4095L;
    return s;
}

// 线程工作范围：以 (块 b, 行组 g) 为单位，块内行组等价，块间按 tile 数加权
typedef struct { long b, g; } pos_t;

static pos_t locate(long s, long NB, long G, const int* TB)
{
    long cum = 0;
    for (long b = 0; b < NB; b++) {
        long bw = G * TB[b];
        if (s < cum + bw) { pos_t p = {b, (s - cum) / TB[b]}; return p; }
        cum += bw;
    }
    pos_t p = {NB, 0};
    return p;
}

// ---------------------------------------------------------------- 工作线程主体（OpenMP 或自有线程池调用）
typedef struct {
    const CONVFLOAT* in; const CONVFLOAT* k; CONVFLOAT* out;
    long H, W, KH, KW, outH, outW;
    long BW, NB, G, NS, RS, m4, rem, PW, slot_floats, ring_stride, Wtot;
    long KPS, br_pre, br_post;       // Kp 行距（float）；边界行方案去掉的首/尾行数（0 = 不用）
    int SP, prof, pf_in, pf_out, pool, slice_ovl, postart_env, store_asm, pf_l2;
    int rpacked;               // 1 = R/Kp 已由主线程打包（kernel 与上次相同，缓存命中），工作线程不打包、无起始屏障
    const int* TB; uint64_t c_pre; prof_t* prs; uint64_t call_id;
    int mode; const void* rp;  // mode 1 = 滚动形态（rp 指向 rplan_t）
} ctx_t;

// ---- 边界行（BR）方案的辅助：sweep 队列、ZA 初值装入、ZA 抽取
// 追加输出行 jc 的 sweep 序列：kernel 行 kj0..kj1 升序（保持累加顺序），输入行 = row0 + kj + 3 - jc；
// 首个 sweep 初值 src0（NULL = 0），中间结果经 stash（16 向量）；末个 sweep：final_out 非空 → st4w 到输出，否则存 stash
// tab = 槽表（2NS+1 项，从行 rbase 对应的槽开始），行 rbase + d 的平面 0 地址 = tab[d]（免每次取模：udiv 十几周期 × 12 次/pass）
static int sw_add(swd_t* q, int n, long jc, long kj0, long kj1, long d0, const uint64_t* tab, long poff,
                  const float* Kp, long KPS, const float* src0, float* stash, char* final_out, long ntile)
{
#ifdef CONV_NOHALF   // 仅供归因诊断：不排任何 sweep（边界行结果错误），量 BR 主循环 + ZA 初值/抽取本身的代价
    (void)jc; (void)kj0; (void)kj1; (void)d0; (void)tab; (void)poff; return n;
#endif
    for (long kj = kj0; kj <= kj1; kj++) {
        q[n].ntile = ntile;
        q[n].abase = (char*)(uintptr_t)tab[d0 + kj + 3 - jc] + poff;
        q[n].kq = Kp + kj * KPS;
        q[n].src = (kj == kj0) ? src0 : (const float*)1;      // 1 = 沿用上一 sweep 的累加器（链式，免暂存往返）
        const int last = (kj == kj1);
        q[n].dst = (last && final_out) ? final_out : (char*)stash;
        q[n].kind = !last ? 2 : (final_out ? 1 : 0);          // 2 = 不存（下一 sweep 接着累加）
        n++;
    }
    return n;
}
// 暂存区 16 向量的布局 [t][i]（i ↔ ic = 3-i，与 st4w 列序一致）；ZA 竖切片 c = 4*ic + jc = 4*(3-i) + jc
#define ZA_INIT_TILE(T)                                                                                   \
    asm volatile("ptrue p0.s\n\t add w12, %w[jc], #12\n\t add w13, %w[jc], #8\n\t add w14, %w[jc], #4\n\t mov w15, %w[jc]\n\t" \
                 "ld1w {z0.s}, p0/z, [%[s]]\n\t ld1w {z1.s}, p0/z, [%[s], #1, mul vl]\n\t"                  \
                 "ld1w {z2.s}, p0/z, [%[s], #2, mul vl]\n\t ld1w {z3.s}, p0/z, [%[s], #3, mul vl]\n\t"      \
                 "mova za" #T "v.s[w12, 0], p0/m, z0.s\n\t mova za" #T "v.s[w13, 0], p0/m, z1.s\n\t"        \
                 "mova za" #T "v.s[w14, 0], p0/m, z2.s\n\t mova za" #T "v.s[w15, 0], p0/m, z3.s\n\t"        \
                 : : [jc] "r"(jc), [s] "r"(src) : "memory", "x12", "x13", "x14", "x15", "z0", "z1", "z2", "z3", "p0")
static inline void za_init_row(int t, int jc, const float* src)
{
    switch (t) { case 0: ZA_INIT_TILE(0); break; case 1: ZA_INIT_TILE(1); break; case 2: ZA_INIT_TILE(2); break; default: ZA_INIT_TILE(3); break; }
}
#define ZA_EXTRACT_TILE(T)                                                                                \
    asm volatile("ptrue p0.s\n\t add w12, %w[jc], #12\n\t add w13, %w[jc], #8\n\t add w14, %w[jc], #4\n\t mov w15, %w[jc]\n\t" \
                 "mova z0.s, p0/m, za" #T "v.s[w12, 0]\n\t mova z1.s, p0/m, za" #T "v.s[w13, 0]\n\t"        \
                 "mova z2.s, p0/m, za" #T "v.s[w14, 0]\n\t mova z3.s, p0/m, za" #T "v.s[w15, 0]\n\t"        \
                 "st1w {z0.s}, p0, [%[d]]\n\t st1w {z1.s}, p0, [%[d], #1, mul vl]\n\t"                      \
                 "st1w {z2.s}, p0, [%[d], #2, mul vl]\n\t st1w {z3.s}, p0, [%[d], #3, mul vl]\n\t"          \
                 : : [jc] "r"(jc), [d] "r"(dst) : "memory", "x12", "x13", "x14", "x15", "z0", "z1", "z2", "z3", "p0")
static inline void za_extract_row(int t, int jc, float* dst)
{
    switch (t) { case 0: ZA_EXTRACT_TILE(0); break; case 1: ZA_EXTRACT_TILE(1); break; case 2: ZA_EXTRACT_TILE(2); break; default: ZA_EXTRACT_TILE(3); break; }
}

static void conv_worker(int tid, int nt_, const ctx_t* c)
{
    const CONVFLOAT* in = c->in; const CONVFLOAT* k = c->k; CONVFLOAT* out = c->out;
    const long H = c->H, W = c->W, KH = c->KH, KW = c->KW, outH = c->outH, outW = c->outW;
    const long BW = c->BW, NB = c->NB, G = c->G, NS = c->NS, RS = c->RS, m4 = c->m4, rem = c->rem, PW = c->PW;
    const long slot_floats = c->slot_floats, ring_stride = c->ring_stride, Wtot = c->Wtot;
    const int prof = c->prof, pf_in = c->pf_in, pf_out = c->pf_out, pool = c->pool, slice_ovl = c->slice_ovl;
    const int postart_env = c->postart_env;
    const int store_asm = c->store_asm && m4 >= STORE_MIN_M4;   // 承载回写的块组每行都要执行到
    const int pf_l2 = c->pf_l2;
    const int* TB = c->TB; const uint64_t c_pre = c->c_pre; prof_t* prs = c->prs;
    const long KPS = c->KPS, br_pre = c->br_pre, br_post = c->br_post;
    (void)BW; (void)c_pre;
    if (!pool) pin_self(tid);                     // 池线程创建时已绑核；OpenMP 线程每次重绑
    prof_t pr = {0, 0, 0, 0, 0, 0, 0, 0};
    uint64_t t0 = 0, t1 = 0, t_start = 0;
    if (prof) { t_start = cyc(); pr.enter = t_start - c_pre; }
    if (prof) pr.cpu = (uint64_t)sched_getcpu();      // 系统调用 ~20 µs，放在 enter 计时之后（否则 enter 全被它撑大）

    // 1) 主线程打包 kernel：R[Y][X'][jc] = kpad[Y-3+jc][X'-3]（30–60 µs，与其他线程的唤醒重叠；
    //    不用 barrier：早到的线程等标志，晚到的线程的工作项会被别人偷走）
    pos_t ps = locate(Wtot * tid / nt_, NB, G, TB);
    pos_t pe = locate(Wtot * (tid + 1) / nt_, NB, G, TB);
    {
        uint64_t n0 = (uint64_t)(ps.b * G + ps.g), n1 = (uint64_t)(pe.b * G + pe.g);
        __atomic_store_n(&g_work[tid].w, (n1 << 32) | n0, __ATOMIC_RELEASE);
    }
    if (!c->rpacked) {
        // 各线程打包自己的一段 Y，然后计数屏障。共享判题机上这道屏障会把某个被分时线程的一个调度时间片（本机 12 ms）
        // 传给全体，因此正常路径（kernel 与上次相同）由主线程在唤醒线程池之前打包并缓存，这里不再执行。
        const long y0 = NS * tid / nt_, y1 = NS * (tid + 1) / nt_;
        for (long Y = y0; Y < y1; Y++) {
            float* r = g_R + Y * RS;
            for (long Xp = 0; Xp < KW + 6; Xp++) {
                long x = Xp - 3;
                for (int jc = 0; jc < 4; jc++) {
                    long y = Y - 3 + jc;
                    r[Xp * 4 + jc] = (y >= 0 && y < KH && x >= 0 && x < KW) ? k[y * KW + x] : 0.0f;
                }
            }
        }
        if (br_pre) {   // Kp：零填充 kernel 行（fmla 扫描的 ld1rqw 读 Kp[kj][X'..X'+3]）
            const long k0 = KH * tid / nt_, k1 = KH * (tid + 1) / nt_;
            for (long kj = k0; kj < k1; kj++) {
                float* r = g_Kp + kj * KPS;
                for (long z = 0; z < KPS; z++) r[z] = (z >= 3 && z < KW + 3) ? k[kj * KW + z - 3] : 0.0f;
            }
        }
        __atomic_fetch_add(&g_rcount.v, 1, __ATOMIC_ACQ_REL);
        while (__atomic_load_n(&g_rcount.v, __ATOMIC_ACQUIRE) < (uint64_t)nt_) asm volatile("yield" ::: "memory");
    }
    float* P = g_P + (size_t)tid * ring_stride;
    float tmp[4 * 64] __attribute__((aligned(256)));
    char dummy[4 * 640 + 64] __attribute__((aligned(64)));   // 切片哑目标（4 个平面 × 最大 PWb）
    // 槽表：tab[i] = 槽 (i mod NS) 的平面 0 字节地址，2NS+1 项，使从任意起点连续走 NS+1 项（含末行预载）无需取模
    uint64_t* slot_tab = g_tab + (size_t)tid * g_tab_stride;
    for (long i = 0; i < 2 * NS + 1; i++) slot_tab[i] = (uint64_t)(uintptr_t)(P + (i % NS) * slot_floats);
    if (g_knobs.diag_l1) for (long i = 0; i < 2 * NS + 1; i++) slot_tab[i] = (uint64_t)(uintptr_t)P;   // 诊断：a 全走槽 0（L1 驻留，结果错误）
    const float* R = g_R;
    const long sht = (((m4 - 1) & 15) + 1) * 4;    // 尾步相对对齐基址的字节偏移
    const long chunks = (m4 + 14) / 16;            // 每行执行切片的块组数（最后一块组若只含块 0 则不执行切片）
    // pass 参数：不随 pass 变化的字段只填一次（pass 之间的 C 代码越少越好：fmopa 空转）
    pass_t pa;
    memset(&pa, 0, sizeof(pa));
    pa.pbrow = R; pa.Y = NS; pa.rowts = NULL; pa.zi[0] = pa.zi[1] = NULL; pa.zx[0] = pa.zx[1] = NULL;
    pa.PWb = PW * 4; pa.PW2b = PW * 8; pa.PW3b = PW * 12; pa.RSB = g_knobs.diag_l1 >= 2 ? 0 : RS * 4; /* 诊断 2：b 只读 R 行 0 */ pa.m4 = m4; pa.rem = rem; pa.sht = sht;
    pa.istride = (long)W * 4; pa.ostride = outW * 4;
    pa.sdummy = dummy; pa.sdcnt = chunks;
    // 边界行方案：每线程暂存（按 pass 序号 p）——前半初值 pre_st[p][3-jc]、后半抽取 post_st[p][jc]，各 16 向量；
    // sweep 描述符队列；上一组待续的后半（pend）；下一组前半是否已算好（pre_ok）
    float pre_st[3][2][16][16] __attribute__((aligned(64)));
    float post_st[3][2][16][16] __attribute__((aligned(64)));
    swd_t swq[16] __attribute__((aligned(64)));
    struct { long j0, c0, nt; int valid; } pend[3] = {{0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}};
    int pre_ok[3] = {0, 0, 0};
    const float* Kp = g_Kp;
    pa.sw_len = 4 * (KW + 3);
#define SW_ARM() do { pa.swq = swq; pa.sw_xc = swq[0].abase; pa.sw_xk = (const char*)swq[0].kq; \
                      pa.sw_kend = pa.sw_xk + pa.sw_len; pa.sw_half = 0; } while (0)
    pa.inc[0] = pa.inc[1] = pa.inc[2] = PW * 4; pa.inc[3] = -3 * PW * 4 + 4;
    pa.swq = swq; swq[0].abase = NULL;
    // 待续后半的独立排空（下一项不连续 / 没有下一项时）：环形缓冲此刻仍是上一组的内容
#define DRAIN_PENDING()                                                                                        \
    for (int p_ = 0; p_ < 3; p_++) if (pend[p_].valid) {                                                        \
        int qn_ = 0; const long j0p_ = pend[p_].j0, c0p_ = pend[p_].c0; const uint64_t* tb_ = slot_tab + (j0p_ % NS); \
        if (br_post == 2) qn_ = sw_add(swq, qn_, 1, KH - 1, KH - 1, 0, tb_, 256 * p_, Kp, KPS,                    \
                                       post_st[p_][1][0], post_st[p_][1][0], (char*)(out + (j0p_ + 2) * outW + c0p_), pend[p_].nt); \
        qn_ = sw_add(swq, qn_, 0, KH - br_post, KH - 1, 0, tb_, 256 * p_, Kp, KPS,                                \
                     post_st[p_][0][0], post_st[p_][0][0], (char*)(out + (j0p_ + 3) * outW + c0p_), pend[p_].nt);      \
        swq[qn_].abase = NULL; SW_ARM();                                                                     \
        sweep_drain(&pa); pend[p_].valid = 0;                                                                   \
    }

    sme_start();
    long last_b = -1, last_g = -2, built = 0, last_n = -2;
    int victim = tid;
    for (;;) {
        // 认领下一项：先从自己的范围，空了就去偷。
        // 全部用 relaxed：工作项之间没有数据依赖（输入只读、环形缓冲每线程私有、输出区域不重叠），结果的可见性由
        // 结束时的 g_done（acq_rel）保证；若这里用 release，CAS 要等前一 pass 刚发出的 st4w（输出线 RFO）全部落地
        // 才能完成，每 pass 白等 ~200 周期（k81 上比整个回写相还贵）。
        long n = -1;
        for (;;) {
            uint64_t w = __atomic_load_n(&g_work[tid].w, __ATOMIC_RELAXED);
            uint64_t cur = w & 0xffffffffu, end = w >> 32;
            if (cur >= end) break;
            if (__atomic_compare_exchange_n(&g_work[tid].w, &w, w + 1, 0, __ATOMIC_RELAXED, __ATOMIC_RELAXED)) { n = (long)cur; break; }
        }
        if (n < 0) {
            int found = 0;
            for (int kk = 1; kk < nt_ && !found; kk++) {
                int v = (victim + kk) % nt_;
                for (;;) {
                    uint64_t w = __atomic_load_n(&g_work[v].w, __ATOMIC_RELAXED);
                    uint64_t cur = w & 0xffffffffu, end = w >> 32;
                    if (end <= cur + 1) break;                 // 不足 2 项不偷
                    uint64_t mid = (cur + end + 1) / 2;
                    if (__atomic_compare_exchange_n(&g_work[v].w, &w, (mid << 32) | cur, 0, __ATOMIC_RELAXED, __ATOMIC_RELAXED)) {
                        __atomic_store_n(&g_work[tid].w, (end << 32) | mid, __ATOMIC_RELAXED);
                        victim = v; found = 1; if (prof) pr.steals++; break;
                    }
                }
            }
            if (!found) { DRAIN_PENDING(); break; }
            continue;
        }
        long b, g;   // n = b*G + g；静态范围连续递增时免除法（两次整数除法 ~40 周期/pass）
        if (n == last_n + 1) { g = last_g + 1; b = last_b; if (g == G) { g = 0; b++; } } else { b = n / G; g = n % G; }
        last_n = n;
        if (prof) pr.items++;
        const long i0 = b * BW;
        const long ntiles = TB[b];
        const long npass = (ntiles + 3) / 4;
        const long ncols = W - i0;                 // 该块可读的输入列数
        const long j0 = 4 * g;
        const int fresh = (b != last_b || g != last_g + 1);
        if (fresh) {                               // 换块/不连续：先把上一组待续的后半算完（还要用旧环），再重建环形缓冲
            DRAIN_PENDING();
            pre_ok[0] = pre_ok[1] = pre_ok[2] = 0;
            built = j0;
        }
        last_b = b; last_g = g;
        // 构建本组需要的新输入行（环形槽 = row % NS）
        if (prof) t0 = cyc();
        if (fresh && g_pf_fresh) {
            // 整环重建（范围起点/窃取后）要从 DRAM 读 NS 行：先把所有行的线都发出预取，靠 MLP 遮延迟（否则逐行串行取数）
            const long bytes = (ncols < 4 * PW ? ncols : 4 * PW) * 4;
            for (long rr = j0; rr < j0 + NS && rr < H; rr++) {
                const char* q = (const char*)(in + rr * (long)W + i0);
                for (long o = 0; o < bytes; o += 64) __builtin_prefetch(q + o, 0, 3);
            }
        }
        for (; built < j0 + NS; built++) {
            const float* src = (built < H) ? in + built * (long)W + i0 : NULL;
            build_planes(src, ncols, PW, P + (built % NS) * slot_floats);
        }
        if (prof) { t1 = cyc(); pr.build += t1 - t0; }
        // 预取规划（在 pass 的 asm 里用游标逐行发出）：下一组新增的 4 个原始输入行 + 本组输出行
        const long rowb_in = (ncols < 4 * PW ? ncols : 4 * PW) * 4;   // 每输入行字节
        // 切片重叠时，本组构建的是行 j0+NS..+3（应在上一组预取），所以本组预取再往后 4 行；范围起点补一轮
        const long pfi_row0 = j0 + NS + (slice_ovl ? 4 : 0);
        if (slice_ovl && pf_in && fresh) {
            for (long rr = j0 + NS; rr < j0 + NS + 4 && rr < H; rr++) {
                const char* q = (const char*)(in + rr * (long)W + i0);
                for (long o = 0; o < rowb_in; o += 64) __builtin_prefetch(q + o, 0, 3);
            }
        }
        const float* pfi = (pf_in && pfi_row0 < H) ? in + pfi_row0 * (long)W + i0 : NULL;
        const long pfi_rows = pfi ? ((H - pfi_row0) < 4 ? (H - pfi_row0) : 4) : 0;
        const long pfi_rowl = (rowb_in + 63) / 64 + 1;               // 起点按 64 B 向下取整，多取 1 线覆盖
        const long orows = (outH - j0) < 4 ? (outH - j0) : 4;
        pa.stab = slot_tab + (j0 % NS);            // 切片目标槽表（2NS 项）
        const uint64_t* tab0 = pa.stab;            // 行 j0+d 的槽地址 = tab0[d]（d ∈ [-4, NS]：上一组后半用到 j0-4+KH+1 ≥ j0+4）
        for (long p = 0; p < npass; p++) {
            const long nt = (ntiles - 4 * p) < 4 ? (ntiles - 4 * p) : 4;
            const long c0 = i0 + 256 * p;
            const long rowb_out = ((outW - c0) < 64 * nt ? (outW - c0) : 64 * nt) * 4;
#ifdef CONV_ZVA_CURSOR
            const int zva = g_knobs.zva;
#else
            const int zva = 0;
#endif
            // zva：只清本 pass 独占的整线。行段 [A_r, A_r+rowb)，A_r = A_0 + r*outW*4 未必 64 B 对齐（行距不是 64 的倍数时
            // 逐行漂移），游标按固定行距推进，所以两端各留 1 线余量：起点 ceil64(A_0)+64，每行 floor(rowb/64)-2 线（取偶）
            long pfo_rowl = pf_out ? (rowb_out + 63) / 64 + 1 : 0;
#ifdef CONV_ZVA_CURSOR   // asm 里游标固定是 dc zva：不能清零时（CONV_ZVA=0 / 硬件禁止）整个游标关掉
            pfo_rowl = (pf_out && zva) ? (rowb_out / 64 - 2) & ~1L : 0; if (pfo_rowl < 2) pfo_rowl = 0;
#endif
            if (prof) t0 = cyc();
            pa.poff = 256 * p;                        // 第 p 个 pass 的平面起点
            // 边界行方案：4 个整 tile、4 行输出都有效时，Y 循环只跑 [br_pre, KH+2-br_post]；
            // 去掉的首行由 fmla 算成 ZA 初值（jc=3/2 列），尾行在 pass 后抽出 jc=1/0 列用 fmla 续完
            const int br = br_pre && c0 + 64 * nt <= outW && j0 + 3 < outH;   // nt 个 tile 都完整（nt<4 时 tile≥nt 的 sweep 结果不存）
            const long Ymain = br ? NS - br_pre - br_post : NS;
            pa.tab = slot_tab + (j0 % NS) + (br ? br_pre : 0);
            pa.Y = Ymain; pa.pbrow = R + (br ? br_pre : 0) * RS; pa.jcoff = br ? br_post : 0;
            // sweep 队列：上一组同 p 的后半（若连续）+ 下一组同 p 的前半（推测下一项连续；不连续则丢弃重算）
            int qn = 0;
            if (pend[p].valid) {
                const long j0p = pend[p].j0, c0p = pend[p].c0;
                if (br_post == 2) qn = sw_add(swq, qn, 1, KH - 1, KH - 1, -4, tab0, pa.poff, Kp, KPS,
                                              post_st[p][1][0], post_st[p][1][0], (char*)(out + (j0p + 2) * outW + c0p), pend[p].nt);
                qn = sw_add(swq, qn, 0, KH - br_post, KH - 1, -4, tab0, pa.poff, Kp, KPS,
                            post_st[p][0][0], post_st[p][0][0], (char*)(out + (j0p + 3) * outW + c0p), pend[p].nt);
                pend[p].valid = 0;
            }
            if (br && !pre_ok[p]) {   // 范围起点：本组的前半没人算过，先独立算好
                int qf = qn;
                qf = sw_add(swq, qf, 3, 0, br_pre - 1, 0, tab0, pa.poff, Kp, KPS, NULL, pre_st[p][0][0], NULL, nt);
                if (br_pre == 2) qf = sw_add(swq, qf, 2, 0, 0, 0, tab0, pa.poff, Kp, KPS, NULL, pre_st[p][1][0], NULL, nt);
                swq[qf].abase = NULL;
                SW_ARM();
                sweep_drain(&pa);        // 顺带把待续后半也排空了
                qn = 0;
#ifdef CONV_DEBUG_BR
                if (tid == 0 && g_call == 1 && j0 == 0 && p == 0) {   // 对照：tile 0 的 jc=3 初值 vs C 参考
                    for (int i = 0; i < 4; i++) for (int r = 0; r < 3; r++) {
                        const int ic = 3 - i; const long col = c0 + 4 * r + 3 - ic;
                        float ref = 0;
                        for (long kj = 0; kj < br_pre; kj++) for (long ki = 0; ki < KW; ki++) ref = __builtin_fmaf(in[(j0 + kj) * W + col + ki], k[kj * KW + ki], ref);
                        fprintf(stderr, "  pre jc3 t0 i%d r%d col %ld: got %.6f ref %.6f\n", i, r, col, pre_st[p][0][i][r], ref);
                    }
                    for (int i = 0; i < 4; i++) { const int ic = 3 - i; const long col = c0 + 3 - ic; float ref = 0;
                        for (long ki = 0; ki < KW; ki++) ref = __builtin_fmaf(in[(j0 + 1) * W + col + ki], k[ki], ref);
                        fprintf(stderr, "  pre jc2 t0 i%d r0 col %ld: got %.6f ref %.6f\n", i, col, pre_st[p][1][i][0], ref); }
                    fprintf(stderr, "  abase0 %p slot0 %p PWb %ld inc %ld %ld %ld %ld kq %p Kp %p KPS %ld len %ld\n", (void*)swq[0].abase,
                            (void*)P, pa.PWb, pa.inc[0], pa.inc[1], pa.inc[2], pa.inc[3], (void*)swq[0].kq, (void*)Kp, KPS, pa.sw_len);
                }
#endif
            }
            pre_ok[p] = 0;
            if (br && g + 1 < G && j0 + 4 + 3 < outH) {
                qn = sw_add(swq, qn, 3, 0, br_pre - 1, 4, tab0, pa.poff, Kp, KPS, NULL, pre_st[p][0][0], NULL, nt);
                if (br_pre == 2) qn = sw_add(swq, qn, 2, 0, 0, 4, tab0, pa.poff, Kp, KPS, NULL, pre_st[p][1][0], NULL, nt);
                pre_ok[p] = 1;
            }
            swq[qn].abase = NULL;
            SW_ARM();
            // 半步密度：稀疏（每块组 1 个，2 fmla/步）容量 = Ymain*m4/2 个 X'；放不下才用稠密（每 8 步 3 个）；放不完的由 pass 末排空兜底
            pa.sw_dense = g_knobs.sw_dense >= 0 ? g_knobs.sw_dense : (2 * qn * (KW + 3) > Ymain * m4);
            // ZA：清零后装入前半初值（jc=3 各 tile 的 4 个竖切片，br_pre=2 时还有 jc=2）
            // ZA：序言里清零后装入前半初值（jc=3 各 tile 的 4 个竖切片，br_pre=2 时还有 jc=2）；尾声抽出 jc<br_post 的行到暂存区
            // ZA 初值在 asm 序言装入（与 C 里装入等速，代码更直）；抽取仍在 C（放进 asm 尾声实测 k41 −0.6%：紧跟末尾 fmopa 的 mova 要等流水排空）
            pa.zi[0] = br ? pre_st[p][0][0] : NULL; pa.zi[1] = (br && br_pre == 2) ? pre_st[p][1][0] : NULL;
            pa.zx[0] = pa.zx[1] = NULL;
            // 输入预取游标：pfi_rows 行，每行 pfi_rowl 线，行距 W*4（只在第一个 pass 做）
            pa.pi = pa.pie = (const char*)in; pa.pin = 0; pa.ijump = 0;
            if (pfi && p == 0) {
                pa.pi = (const char*)((uintptr_t)pfi & ~(uintptr_t)63);
                pa.pie = pa.pi + pfi_rowl * 64;
                pa.pin = pfi_rows * pfi_rowl;
                pa.ijump = (long)W * 4 - pfi_rowl * 64;
            }
            // 输出预取游标：orows 行，每行 pfo_rowl 线，行距 outW*4
            pa.po = pa.poe = (const char*)out; pa.pon = 0; pa.ojump = 0;
            if (pfo_rowl) {
                pa.po = zva ? (const char*)((((uintptr_t)(out + j0 * outW + c0) + 63) & ~(uintptr_t)63) + 64)
                            : (const char*)((uintptr_t)(out + j0 * outW + c0) & ~(uintptr_t)63);
                pa.poe = pa.po + pfo_rowl * 64;
                pa.pon = orows * pfo_rowl;
                pa.ojump = outW * 4 - pfo_rowl * 64;
            }
            // 切片构建（最后一个 pass）：把下一组 4 个新行的整切片穿插进本 pass 的行循环；尾切片/越界行由 C 补。
            // 每行有 ceil(m4/16) 个块组、每块组一片；Y=0 期间槽 j0 仍被读 → 前 ceil(m4/16) 片写哑区。
            long s_nfull = 0, s_rows = 0;
            if (p == npass - 1 && built == j0 + NS && slice_ovl) {
                s_nfull = (W - i0) / 64; if (s_nfull > PW / 16) s_nfull = PW / 16;
                s_rows = (H - (j0 + NS)) < 4 ? (H - (j0 + NS)) : 4;
                if (s_rows < 0) s_rows = 0;
                if (s_nfull < chunks || chunks < 1 || m4 < 2 || chunks + s_rows * s_nfull > Ymain * chunks ||
                    3 * PW * 4 + 64 * chunks + 64 > (long)sizeof(dummy)) { s_nfull = 0; s_rows = 0; }
            }
            pa.snfull = s_nfull; pa.srows = s_rows ? s_rows + 1 : 0;
            pa.sjump = (long)W * 4 - s_nfull * 256;
            pa.ssrc = (const char*)(in + (j0 + NS) * (long)W + i0) - 256 * chunks - pa.sjump;
            // 输出预取集中在最后 ~rows 行（每行 4 条）：lines/4 + 2 行，至少 4 行；不超过行数
            { long rows = pa.pon / 4 + 2; if (rows < 4) rows = 4; if (rows > Ymain) rows = Ymain; pa.postart = postart_env > 0 ? postart_env : rows; }
            if (zva && pa.pon) {
                // 清零必须先于同一线的存储：pass 内最早的回写是 jc'=3 行（剩余行数 x14 = 3 - jcoff），游标每行 4 线，
                // 要求全部 pon 线在那之前清完：postart ≥ pon/4 + (3 - jcoff) + 1；pass 太短放不下 → 本 pass 不清零（普通 RFO）
                const long need = (pa.pon + 3) / 4 + (3 - pa.jcoff) + 1;
                if (need > Ymain) { pa.pon = 0; pa.po = NULL; }
                else pa.postart = (postart_env >= need && postart_env <= Ymain) ? postart_env : need;
            }
            // asm 内回写：目标 = 输出行 j0 起点（整 tile）或 tmp（末尾不满 64 列的 tile，行距 256 B）；
            // 行组末尾有越界行（j0+3 ≥ outH）时不用（一块只有一组，走 C 路径）。
            // 经典：jc=3/2/1 在 pass 内、jc=0 由 C；边界行：jc=3..br_post+1 在 pass 内、jc=br_post 由 C、jc<br_post 走 sweep
            const int asm_rows = (store_asm && j0 + 3 < outH) ? 3 : 0;
            for (long t = 0; t < 4; t++) {
                const long col0 = c0 + 64 * t;
                const int full = (col0 + 64 <= outW);
                char* base = full ? (char*)(out + j0 * outW + col0) : (char*)tmp;
                pa.sdst[t] = (t < nt && asm_rows) ? base : NULL;
                pa.sstr[t] = full ? outW * 4 : 256;
                pa.pfst[t] = (g_knobs.pf_st && t < nt && full && j0 + 3 < outH) ? base : NULL;   // 回写前一行的 L1 预取（tmp 不必预取）
            }
#ifdef CONV_ROWPROF
            pa.rowts = (tid == 0 && c->call_id == 2 && g_rowts_cur && g_rowts_cur + NS + 4 < g_rowts_end) ? g_rowts_cur : NULL;
            if (pa.rowts) *pa.rowts++ = cyc() | (2ull << 60);   // 标记 2：pass 前 C 准备完毕，进入 pass_steps
#endif
            pass_steps((int)nt, &pa, pf_l2);
#ifdef CONV_ROWPROF
            if (pa.rowts) { *pa.rowts++ = cyc() | (1ull << 63); g_rowts_cur = pa.rowts; }
#endif
            if (s_rows) {
                // 补：每行的尾切片（列 ≥ 64*s_nfull）与越界行的清零；然后这 4 行算已构建
                for (long i = 0; i < 4; i++) {
                    const long rr = j0 + NS + i;
                    float* slot = P + (rr % NS) * slot_floats;
                    if (i < s_rows) {
                        const float* src = in + rr * (long)W + i0;
                        for (long x0 = s_nfull * 16; x0 < PW; x0 += 16) build_slice(src, ncols, PW, slot, x0);
                    } else {
                        build_planes(NULL, 0, PW, slot);
                    }
                }
                built = j0 + NS + 4;
            }
            if (prof) { t1 = cyc(); pr.kern += t1 - t0; t0 = t1; }
            // 边界行：抽出 jc<br_post 的列（4 竖切片/tile）到暂存区，留给下一 pass 期间的 sweep 续完
            const int jc_lo = br ? (int)br_post : 0;
            if (br) {
                for (int t = 0; t < 4; t++) za_extract_row(t, 0, post_st[p][0][4 * t]);
                if (br_post == 2) for (int t = 0; t < 4; t++) za_extract_row(t, 1, post_st[p][1][4 * t]);
                pend[p].valid = 1; pend[p].j0 = j0; pend[p].c0 = c0; pend[p].nt = nt;
            }
            // 回写：tile t 行 j0+3-jc，列 c0+64t（pass 内已存出的行不再存）
            for (long t = 0; t < nt; t++) {
                const long col0 = c0 + 64 * t;
                const int full = (col0 + 64 <= outW);
                for (int jc = asm_rows ? jc_lo : 3; jc >= jc_lo; jc--) {
                    const long row = j0 + 3 - jc;
                    if (row >= outH) continue;
                    if (full) store_tile_row_out((int)t, jc, out + row * outW + col0);
                    else store_tile_row((int)t, jc, tmp + (3 - jc) * 64);
                }

                if (!full) {
                    const long nvalid = outW - col0;
                    for (int jc = 0; jc < 4; jc++) {
                        const long row = j0 + 3 - jc;
                        if (row >= outH) continue;
                        float* dst = out + row * outW + col0;
                        const float* srcp = tmp + (3 - jc) * 64;
                        for (long x = 0; x < nvalid; x += 16) {
                            svbool_t pg = svwhilelt_b32((int64_t)x, (int64_t)nvalid);
                            svst1_f32(pg, dst + x, svld1_f32(pg, srcp + x));
                        }
                    }
                }
            }
            if (prof) { t1 = cyc(); pr.store += t1 - t0; }
#ifdef CONV_ROWPROF
            if (pa.rowts) { *pa.rowts++ = cyc() | (1ull << 60); g_rowts_cur = pa.rowts; }   // 标记 1：抽取 + 回写完成
#endif
        }
    }
    sme_stop();
    if (prof) { pr.total = cyc() - t_start; prs[tid] = pr; }
}

// 诊断包装：探针都放在 conv_worker 之外（不改变热路径的代码生成）；系统调用在流式模式外做

// ================================================================ 滚动形态（16×1 为主）
// 思路：tile 行 r ↔ 连续 16 个输入列（a 直接非对齐载入，无 stride-4 平面、无环形缓冲行轮转），tile 列 c ↔ 输出行残差
// (s_base+c) mod KH：每列是一条独立的 fma 链（kj 升序、ki 升序，位精确），链结束时 mova 竖切片直接 st1w 成 16 个连续
// 输出 float，再把该列清零开始下一输出行。步数 = KW（X 方向零浪费），没有 pass 边界、没有边界行 sweep。
// 残差按 KH 的二进制分组：16×1 对（A/B 两组共用 32 列 a）、16×1 单（4 tile 64 列）、8×2（ld2w，4 tile 128 列，
// 步数 KW+1）、1×16（1 个残差 × 16 个 X 偏移，2 计算 tile + 2 转置 tile，步数 KW+15）。
static long g_roll_pd = 3;
static void roll_copy_row(float* dst, const float* src, long n)   // n 个 float，SVE 循环
{
    asm volatile(
        "mov x9, #0\n\t"
        "whilelo p0.s, x9, %[n]\n\t"
        "1:\n\t"
        "ld1w {z0.s}, p0/z, [%[s], x9, lsl #2]\n\t"
        "st1w {z0.s}, p0, [%[d], x9, lsl #2]\n\t"
        "incw x9\n\t"
        "whilelo p0.s, x9, %[n]\n\t"
        "b.first 1b\n\t"
        : : [s]"r"(src), [d]"r"(dst), [n]"r"(n) : "x9", "z0", "p0", "memory", "cc");
}
// 内核参数（asm 内从结构体装载，避免操作数过多）
//  行数据先由 prfm pldl2keep 提前 PD 行进 L2，再在处理第 Y 行时把第 Y+1 行的段拷进 L1 环（2 槽），a 从环取：
//  避免行距 16/24 KB 与 L1 组混叠（每行落在同一组，PD 行同时在 L1 会互相逐出）。
typedef struct {
    int64_t in_row, rsb, R, Rend, bA, bB, KH, steps, nrows, out, scr, cA0, cB0, va, nvA, nvB, pf, it, PD, ring, slot, ncp_full, ncp_tail, n2, e2, TSB, T, nlines, osb, pfo, sh4, kb2, cf2, kw4, khkw4;
} ka_t;
typedef struct {
    const float* in_row; long rsb; const float* R; long RSB; long KH, steps, nrows;
    float* out_row0; float* scratch; long cA0, cB0, yA0, yB0, nvA, nvB; float* ring; long KW; long osb;   // osb: 输出行距（字节）
    const float* kb0; const float* kbase; const float* kend; long cf0;   // pair+fmla：第 33 残差的 kernel 行游标与事件计数值
    const float* kb20; long cf20;                                         // single16+2fmla：第二条 fmla 残差
} kp_t;
static void fill_args(ka_t* A, const kp_t* P, long div, long slot_unused, long ncp)
{
    (void)slot_unused;
    // 拷贝源对齐到 64 B：ld1w/st1w 两侧全对齐（否则跨 4 KB 页的非对齐 L2 载入每行 +40 周期，
    // 且非对齐 L2 命中 2.5 周期/条）；a 基址 = 槽 + sh4。
    const long sh = ncp ? (((uintptr_t)P->in_row >> 2) & 15) : 0;
    const float* src = P->in_row - sh;
    ncp += sh;
    const long slot = ncp ? ((ncp * 4 + 63) & ~63L) : 0;
    A->ncp_full = ncp / 16; A->ncp_tail = ncp % 16;
    A->sh4 = sh * 4;
    A->in_row = (int64_t)src; A->rsb = P->rsb; A->R = (int64_t)P->R; A->Rend = (int64_t)(P->R + P->KH * P->RSB / 4);
    A->bA = (int64_t)(P->R + P->yA0 * P->RSB / 4); A->bB = (int64_t)(P->R + P->yB0 * P->RSB / 4);
    A->KH = P->KH; A->steps = P->steps; A->nrows = P->nrows; A->out = (int64_t)P->out_row0; A->scr = (int64_t)P->scratch;
    A->cA0 = P->cA0; A->cB0 = P->cB0; A->va = P->KH - 1; A->nvA = P->nvA; A->nvB = P->nvB; A->pf = g_roll_pd * P->rsb; A->it = P->steps / div; A->PD = g_roll_pd;
    A->ring = (int64_t)P->ring; A->slot = slot; A->osb = P->osb; A->pfo = g_roll_pd * P->osb;
    if (ncp) roll_copy_row(P->ring, src, ncp);   // 第 0 行进槽 0；K4 自己做去交织拷贝
}
// 寄存器约定：x0 行指针(输入) x1 rsb x2 bA x3 bB x4 R x5 Rend x6 KH x7 steps/it x8 行计数 x9 out 行 x10 scr x11 Y x12/x13 切片号
//  x14 va x15 步计数 x16 a 指针(环槽) x17 环槽当前 x19 cB x20 out/scr 选择 x21 预取地址 x22/x23 临时 x24 nvA x25 nvB x26 pf x27 cA x28 环基址
#define LOAD_ARGS \
        "ldr x0, [%[A], #0]\n\t" "ldr x1, [%[A], #8]\n\t" "ldr x4, [%[A], #16]\n\t" "ldr x5, [%[A], #24]\n\t" \
        "ldr x2, [%[A], #32]\n\t" "ldr x3, [%[A], #40]\n\t" "ldr x6, [%[A], #48]\n\t" "ldr x7, [%[A], #56]\n\t" \
        "ldr x8, [%[A], #64]\n\t" "ldr x9, [%[A], #72]\n\t" "ldr x10, [%[A], #80]\n\t" "ldr x27, [%[A], #88]\n\t" \
        "ldr x19, [%[A], #224]\n\t" "ldr x14, [%[A], #104]\n\t" "ldr x24, [%[A], #112]\n\t" "ldr x25, [%[A], #120]\n\t" \
        "ldr x26, [%[A], #128]\n\t" "ldr x17, [%[A], #152]\n\t" "ldr x22, [%[A], #160]\n\t" "add x28, x17, x17\n\t" "add x28, x28, x22\n\t" \
        "ldr x22, [%[A], #176]\n\t" "whilelo p3.s, xzr, x22\n\t" "mov x11, #0\n\t" "ptrue p0.s\n\t"
#define XCLOB "x0","x1","x2","x3","x4","x5","x6","x7","x8","x9","x10","x11","x12","x13","x14","x15","x16","x17","x19","x20","x21","x22","x23","x24","x25","x26","x27","x28"
#define ROW_TAIL \
        "add x0, x0, x1\n\t" "add x9, x9, x19\n\t" "add x11, x11, #1\n\t" "subs x8, x8, #1\n\t" "b.ne 1b\n\t"
#define WRAP_B(xb) "cmp " #xb ", x5\n\t" "csel " #xb ", x4, " #xb ", eq\n\t"
#define SEL_OUT "cmp x11, x14\n\t" "csel x20, x9, x10, hs\n\t"
#define ADV_CNT(xc) "add " #xc ", " #xc ", #1\n\t" "cmp " #xc ", x6\n\t" "csel " #xc ", xzr, " #xc ", eq\n\t"
// 行首：L2 预取第 Y+PD 行、把第 Y+1 行（最后一行时拷本行，避免越界）拷到另一槽：ncp_full 个整向量 + 1 个谓词尾向量；x16 = 当前槽
#define ROW_HEAD_COMMON \
        "add x21, x0, x26\n\t" \
        "ldr x12, [%[A], #240]\n\t" \
        "add x16, x17, x12\n\t" \
        "sub x17, x28, x17\n\t" \
        "add x22, x0, x1\n\t" "cmp x8, #1\n\t" "csel x22, x0, x22, eq\n\t" "mov x23, x17\n\t" \
        "ldr x12, [%[A], #168]\n\t" \
        "cbz x12, 7f\n\t" \
        "3:\n\t" \
        "prfm pldl2keep, [x21]\n\t" \
        "ld1w {z24.s}, p0/z, [x22]\n\t" \
        "st1w {z24.s}, p0, [x23]\n\t" \
        "add x21, x21, #64\n\t" "add x22, x22, #64\n\t" "add x23, x23, #64\n\t" \
        "subs x12, x12, #1\n\t" \
        "b.ne 3b\n\t" \
        "7:\n\t" \
        "prfm pldl2keep, [x21]\n\t" \
        "ld1w {z24.s}, p3/z, [x22]\n\t" \
        "st1w {z24.s}, p3, [x23]\n\t"


#define ROW_HEAD_COPY4 \
        "add x21, x0, x26\n\t" \
        "ldr x12, [%[A], #240]\n\t" \
        "add x16, x17, x12\n\t" \
        "sub x17, x28, x17\n\t" \
        "add x22, x0, x1\n\t" "cmp x8, #1\n\t" "csel x22, x0, x22, eq\n\t" "mov x23, x17\n\t" \
        "ldr x12, [%[A], #168]\n\t" \
        "cbz x12, 7f\n\t" \
        "cmp x12, #4\n\t" \
        "b.lo 43f\n\t" \
        "3:\n\t" \
        "prfm pldl2keep, [x21, #0]\n\t" \
        "ld1w {z24.s}, p0/z, [x22]\n\t" \
        "st1w {z24.s}, p0, [x23]\n\t" \
        "prfm pldl2keep, [x21, #64]\n\t" \
        "ld1w {z24.s}, p0/z, [x22, #1, mul vl]\n\t" \
        "st1w {z24.s}, p0, [x23, #1, mul vl]\n\t" \
        "prfm pldl2keep, [x21, #128]\n\t" \
        "ld1w {z24.s}, p0/z, [x22, #2, mul vl]\n\t" \
        "st1w {z24.s}, p0, [x23, #2, mul vl]\n\t" \
        "prfm pldl2keep, [x21, #192]\n\t" \
        "ld1w {z24.s}, p0/z, [x22, #3, mul vl]\n\t" \
        "st1w {z24.s}, p0, [x23, #3, mul vl]\n\t" \
        "add x21, x21, #256\n\t" \
        "add x22, x22, #256\n\t" \
        "add x23, x23, #256\n\t" \
        "sub x12, x12, #4\n\t" \
        "cmp x12, #4\n\t" \
        "b.hs 3b\n\t" \
        "43:\n\t" \
        "cbz x12, 7f\n\t" \
        "44:\n\t" \
        "prfm pldl2keep, [x21]\n\t" \
        "ld1w {z24.s}, p0/z, [x22]\n\t" \
        "st1w {z24.s}, p0, [x23]\n\t" \
        "add x21, x21, #64\n\t" \
        "add x22, x22, #64\n\t" \
        "add x23, x23, #64\n\t" \
        "subs x12, x12, #1\n\t" \
        "b.ne 44b\n\t" \
        "7:\n\t" \
        "prfm pldl2keep, [x21]\n\t" \
        "ld1w {z24.s}, p3/z, [x22]\n\t" \
        "st1w {z24.s}, p3, [x23]\n\t"

// ---------------- 16×1 对：A 用 za0/za1（列 0..15 / 16..31），B 用 za2/za3 ----------------
static void k16pair(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 1, 512, 31 + P->steps);
    asm volatile(
        LOAD_ARGS
        "fmov z31.s, #0.0\n\t"
        "1:\n\t"
        ROW_HEAD_COMMON
        "mov x15, x7\n\t"
        "2:\n\t"
        "ld1w {z0.s}, p0/z, [x16]\n\t"
        "ld1w {z1.s}, p0/z, [x16, #1, mul vl]\n\t"
        "ld1w {z2.s}, p0/z, [x2]\n\t"
        "ld1w {z3.s}, p0/z, [x3]\n\t"
        "fmopa za0.s, p0/m, p0/m, z0.s, z2.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z1.s, z2.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z0.s, z3.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z1.s, z3.s\n\t"
        "add x16, x16, #4\n\t"
        "add x2, x2, #64\n\t"
        "add x3, x3, #64\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        WRAP_B(x2) WRAP_B(x3) SEL_OUT
        // 事件：cA<16 → A 组（za0/za1，切片 cA）；16≤cA<32 → B 组（za2/za3，切片 cA−16）；否则无（KH≥32 时二者互斥）
        "cmp x27, #32\n\t" "b.hs 5f\n\t"
        "cmp x27, #16\n\t" "b.hs 6f\n\t"
        "mov w12, w27\n\t"
        "mova z8.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za1v.s[w12, 0]\n\t"
        "st1w {z8.s}, p0, [x20]\n\t"
        "st1w {z9.s}, p0, [x20, #1, mul vl]\n\t"
        "mova za0v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p0/m, z31.s\n\t"
        "b 5f\n\t"
        "6:\n\t"
        "sub w12, w27, #16\n\t"
        "mova z8.s, p0/m, za2v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za3v.s[w12, 0]\n\t"
        "st1w {z8.s}, p0, [x20]\n\t"
        "st1w {z9.s}, p0, [x20, #1, mul vl]\n\t"
        "mova za2v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za3v.s[w12, 0], p0/m, z31.s\n\t"
        "5:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z8", "z9", "z24", "z31", "p0", "p3", "memory", "cc");
}

static void k16pairf(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 1, 512, 31 + P->steps);
    A.n2 = (int64_t)P->kb0; A.e2 = (int64_t)P->kbase; A.T = (int64_t)P->kend; A.nlines = P->cf0;
    asm volatile(
        LOAD_ARGS
        "ldr x13, [%[A], #184]\n\t"
        "fmov z31.s, #0.0\n\t"
        "fmov z10.s, #0.0\n\t"
        "fmov z11.s, #0.0\n\t"
        "1:\n\t"
        ROW_HEAD_COMMON
        "mov x15, x7\n\t"
        "2:\n\t"
        "ld1w {z0.s}, p0/z, [x16]\n\t"
        "ld1w {z1.s}, p0/z, [x16, #1, mul vl]\n\t"
        "ld1w {z2.s}, p0/z, [x2]\n\t"
        "ld1w {z3.s}, p0/z, [x3]\n\t"
        "fmopa za0.s, p0/m, p0/m, z0.s, z2.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z1.s, z2.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z0.s, z3.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z1.s, z3.s\n\t"
        "ld1rw {z4.s}, p0/z, [x13]\n\t"
        "fmla z10.s, p0/m, z0.s, z4.s\n\t"
        "fmla z11.s, p0/m, z1.s, z4.s\n\t"
        "add x13, x13, #4\n\t"
        "add x16, x16, #4\n\t"
        "add x2, x2, #64\n\t"
        "add x3, x3, #64\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        WRAP_B(x2) WRAP_B(x3)
        "ldr x24, [%[A], #208]\n\t"
        "cmp x13, x24\n\t"
        "ldr x24, [%[A], #192]\n\t"
        "csel x13, x24, x13, eq\n\t"
        SEL_OUT
        // 事件：cA==CF0 → fmla 残差（z10/z11 存出清零）；cA<16 → A；16≤cA<32 → B；其余无
        "ldr x24, [%[A], #216]\n\t"
        "cmp x27, x24\n\t" "b.eq 8f\n\t"
        "cmp x27, #32\n\t" "b.hs 5f\n\t"
        "cmp x27, #16\n\t" "b.hs 6f\n\t"
        "mov w12, w27\n\t"
        "mova z8.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za1v.s[w12, 0]\n\t"
        "st1w {z8.s}, p0, [x20]\n\t"
        "st1w {z9.s}, p0, [x20, #1, mul vl]\n\t"
        "mova za0v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p0/m, z31.s\n\t"
        "b 5f\n\t"
        "6:\n\t"
        "sub w12, w27, #16\n\t"
        "mova z8.s, p0/m, za2v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za3v.s[w12, 0]\n\t"
        "st1w {z8.s}, p0, [x20]\n\t"
        "st1w {z9.s}, p0, [x20, #1, mul vl]\n\t"
        "mova za2v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za3v.s[w12, 0], p0/m, z31.s\n\t"
        "b 5f\n\t"
        "8:\n\t"
        "st1w {z10.s}, p0, [x20]\n\t"
        "st1w {z11.s}, p0, [x20, #1, mul vl]\n\t"
        "fmov z10.s, #0.0\n\t"
        "fmov z11.s, #0.0\n\t"
        "5:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z4", "z8", "z9", "z10", "z11", "z24", "z31", "p0", "p3", "memory", "cc");
}


// ---------------- 16×1 单组：4 tile = 64 列；槽 640 B ----------------
static void k16single(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 1, 640, 63 + P->steps);
    asm volatile(
        LOAD_ARGS
        "fmov z31.s, #0.0\n\t"
        "1:\n\t"
        ROW_HEAD_COMMON
        "mov x15, x7\n\t"
        "2:\n\t"
        "ld1w {z0.s}, p0/z, [x16]\n\t"
        "ld1w {z1.s}, p0/z, [x16, #1, mul vl]\n\t"
        "ld1w {z2.s}, p0/z, [x16, #2, mul vl]\n\t"
        "ld1w {z3.s}, p0/z, [x16, #3, mul vl]\n\t"
        "ld1w {z4.s}, p0/z, [x2]\n\t"
        "fmopa za0.s, p0/m, p0/m, z0.s, z4.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z1.s, z4.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z2.s, z4.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z3.s, z4.s\n\t"
        "add x16, x16, #4\n\t"
        "add x2, x2, #64\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        WRAP_B(x2) SEL_OUT
        "cmp x27, x24\n\t" "b.hs 4f\n\t"
        "and w12, w27, #15\n\t"
        "mova z5.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z6.s, p0/m, za1v.s[w12, 0]\n\t"
        "mova z7.s, p0/m, za2v.s[w12, 0]\n\t"
        "mova z8.s, p0/m, za3v.s[w12, 0]\n\t"
        "st1w {z5.s}, p0, [x20]\n\t"
        "st1w {z6.s}, p0, [x20, #1, mul vl]\n\t"
        "st1w {z7.s}, p0, [x20, #2, mul vl]\n\t"
        "st1w {z8.s}, p0, [x20, #3, mul vl]\n\t"
        "mova za0v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za2v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za3v.s[w12, 0], p0/m, z31.s\n\t"
        "4:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z4", "z5", "z6", "z7", "z8", "z24", "z31", "p0", "p3", "memory", "cc");
}

// ---------------- 16×1 对 + 3 条 fmla 残差（kind 34）：ZA 32 残差 + z10..z15 三条 32 列链 ----------------
// 每步 4 载入 + 3 ld1rw + 4 fmopa + 6 fmla（探针：16 fmopa + 32 fmla = 32 周期，1 fmla/周期免费）。
// 三条链残差 = KH-1, KH-2, KH-3：kj 相差 1 → k 行游标 x13（KH-1）每行派生 x21 = x13+KW4、x22 = x13+2*KW4（回绕各自处理）。
// 事件窗口 [CF0-2, CF0]（CF0 = (KH-1-s_base) mod KH ≥ 36，与 A/B 窗口互斥）。
static void k16pairf4(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 1, 512, 31 + P->steps);
    A.n2 = (int64_t)P->kb0; A.e2 = (int64_t)P->kbase; A.T = (int64_t)P->kend; A.nlines = P->cf0;
    A.kw4 = P->steps * 16;   // kf 每 kernel 行的字节跨度 = steps*4floats*4B
    asm volatile(
        LOAD_ARGS
        "ldr x13, [%[A], #184]\n\t"     // kf 线性游标（起始行 a0）
        "fmov z31.s, #0.0\n\t"
        "fmov z10.s, #0.0\n\t" "fmov z11.s, #0.0\n\t" "fmov z12.s, #0.0\n\t"
        "fmov z13.s, #0.0\n\t" "fmov z14.s, #0.0\n\t" "fmov z15.s, #0.0\n\t"
        "fmov z16.s, #0.0\n\t" "fmov z17.s, #0.0\n\t"
        "1:\n\t"
        ROW_HEAD_COPY4
        "mov x15, x7\n\t"
        ".p2align 4\n"
        "2:\n\t"
        "ld1w {z0.s}, p0/z, [x16]\n\t"
        "ld1w {z1.s}, p0/z, [x16, #1, mul vl]\n\t"
        "ld1w {z2.s}, p0/z, [x2]\n\t"
        "ld1w {z3.s}, p0/z, [x3]\n\t"
        "ld1rqw {z4.s}, p0/z, [x13]\n\t"        // 一次 quadword 广播：z4 各 128 位段 = {kf0,kf1,kf2,0}
        "fmopa za0.s, p0/m, p0/m, z0.s, z2.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z1.s, z2.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z0.s, z3.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z1.s, z3.s\n\t"
        "fmla z10.s, z0.s, z4.s[0]\n\t"          // 按元素索引 fmla（无需单独广播）
        "fmla z11.s, z1.s, z4.s[0]\n\t"
        "fmla z12.s, z0.s, z4.s[1]\n\t"
        "fmla z13.s, z1.s, z4.s[1]\n\t"
        "fmla z14.s, z0.s, z4.s[2]\n\t"
        "fmla z15.s, z1.s, z4.s[2]\n\t"
        "fmla z16.s, z0.s, z4.s[3]\n\t"
        "fmla z17.s, z1.s, z4.s[3]\n\t"
        "add x13, x13, #16\n\t"
        "add x16, x16, #4\n\t"
        "add x2, x2, #64\n\t"
        "add x3, x3, #64\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        WRAP_B(x2) WRAP_B(x3)
        "ldr x24, [%[A], #208]\n\t"              // kf 行回绕（到表尾则回表头）
        "cmp x13, x24\n\t"
        "ldr x24, [%[A], #192]\n\t"
        "csel x13, x24, x13, eq\n\t"
        SEL_OUT
        // 事件：cA ∈ [CF0-3, CF0] → 4 条 fmla 链（w24 = 0:KH-4 / 1:KH-3 / 2:KH-2 / 3:KH-1）；cA<16 → A；16≤cA<32 → B
        "ldr x24, [%[A], #216]\n\t"
        "sub x24, x24, #3\n\t"
        "subs w24, w27, w24\n\t"
        "b.lo 30f\n\t"
        "cmp w24, #3\n\t"
        "b.hi 5f\n\t"
        "b.eq 8f\n\t"
        "cmp w24, #2\n\t"
        "b.eq 9f\n\t"
        "cmp w24, #1\n\t"
        "b.eq 90f\n\t"
        "st1w {z16.s}, p0, [x20]\n\t"
        "st1w {z17.s}, p0, [x20, #1, mul vl]\n\t"
        "fmov z16.s, #0.0\n\t" "fmov z17.s, #0.0\n\t"
        "b 5f\n\t"
        "90:\n\t"
        "st1w {z14.s}, p0, [x20]\n\t"
        "st1w {z15.s}, p0, [x20, #1, mul vl]\n\t"
        "fmov z14.s, #0.0\n\t" "fmov z15.s, #0.0\n\t"
        "b 5f\n\t"
        "9:\n\t"
        "st1w {z12.s}, p0, [x20]\n\t"
        "st1w {z13.s}, p0, [x20, #1, mul vl]\n\t"
        "fmov z12.s, #0.0\n\t" "fmov z13.s, #0.0\n\t"
        "b 5f\n\t"
        "8:\n\t"
        "st1w {z10.s}, p0, [x20]\n\t"
        "st1w {z11.s}, p0, [x20, #1, mul vl]\n\t"
        "fmov z10.s, #0.0\n\t" "fmov z11.s, #0.0\n\t"
        "b 5f\n\t"
        "30:\n\t"
        "cmp x27, #32\n\t" "b.hs 5f\n\t"
        "cmp x27, #16\n\t" "b.hs 6f\n\t"
        "mov w12, w27\n\t"
        "mova z8.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za1v.s[w12, 0]\n\t"
        "st1w {z8.s}, p0, [x20]\n\t"
        "st1w {z9.s}, p0, [x20, #1, mul vl]\n\t"
        "mova za0v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p0/m, z31.s\n\t"
        "b 5f\n\t"
        "6:\n\t"
        "sub w12, w27, #16\n\t"
        "mova z8.s, p0/m, za2v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za3v.s[w12, 0]\n\t"
        "st1w {z8.s}, p0, [x20]\n\t"
        "st1w {z9.s}, p0, [x20, #1, mul vl]\n\t"
        "mova za2v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za3v.s[w12, 0], p0/m, z31.s\n\t"
        "5:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z4", "z8", "z9", "z10", "z11", "z12", "z13", "z14", "z15", "z16", "z17", "z24", "z31", "p0", "p3", "memory", "cc");
}


static void k16pairf3(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 1, 512, 31 + P->steps);
    A.n2 = (int64_t)P->kb0; A.e2 = (int64_t)P->kbase; A.T = (int64_t)P->kend; A.nlines = P->cf0;
    A.kw4 = P->steps * 16;   // kf 每 kernel 行的字节跨度 = steps*4floats*4B
    asm volatile(
        LOAD_ARGS
        "ldr x13, [%[A], #184]\n\t"     // kf 线性游标（起始行 a0）
        "fmov z31.s, #0.0\n\t"
        "fmov z10.s, #0.0\n\t" "fmov z11.s, #0.0\n\t" "fmov z12.s, #0.0\n\t"
        "fmov z13.s, #0.0\n\t" "fmov z14.s, #0.0\n\t" "fmov z15.s, #0.0\n\t"
        "1:\n\t"
        ROW_HEAD_COMMON
        "mov x15, x7\n\t"
        ".p2align 4\n"
        "2:\n\t"
        "ld1w {z0.s}, p0/z, [x16]\n\t"
        "ld1w {z1.s}, p0/z, [x16, #1, mul vl]\n\t"
        "ld1w {z2.s}, p0/z, [x2]\n\t"
        "ld1w {z3.s}, p0/z, [x3]\n\t"
        "ld1rqw {z4.s}, p0/z, [x13]\n\t"        // 一次 quadword 广播：z4 各 128 位段 = {kf0,kf1,kf2,0}
        "fmopa za0.s, p0/m, p0/m, z0.s, z2.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z1.s, z2.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z0.s, z3.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z1.s, z3.s\n\t"
        "fmla z10.s, z0.s, z4.s[0]\n\t"          // 按元素索引 fmla（无需单独广播）
        "fmla z11.s, z1.s, z4.s[0]\n\t"
        "fmla z12.s, z0.s, z4.s[1]\n\t"
        "fmla z13.s, z1.s, z4.s[1]\n\t"
        "fmla z14.s, z0.s, z4.s[2]\n\t"
        "fmla z15.s, z1.s, z4.s[2]\n\t"
        "add x13, x13, #16\n\t"
        "add x16, x16, #4\n\t"
        "add x2, x2, #64\n\t"
        "add x3, x3, #64\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        WRAP_B(x2) WRAP_B(x3)
        "ldr x24, [%[A], #208]\n\t"              // kf 行回绕（到表尾则回表头）
        "cmp x13, x24\n\t"
        "ldr x24, [%[A], #192]\n\t"
        "csel x13, x24, x13, eq\n\t"
        SEL_OUT
        // 事件：cA ∈ [CF0-2, CF0] → fmla 链（w24 = 0:KH-3 / 1:KH-2 / 2:KH-1）；cA<16 → A；16≤cA<32 → B
        "ldr x24, [%[A], #216]\n\t"
        "sub x24, x24, #2\n\t"
        "subs w24, w27, w24\n\t"
        "b.lo 30f\n\t"
        "cmp w24, #2\n\t"
        "b.hi 5f\n\t"
        "b.eq 8f\n\t"
        "cmp w24, #1\n\t"
        "b.eq 9f\n\t"
        "st1w {z14.s}, p0, [x20]\n\t"
        "st1w {z15.s}, p0, [x20, #1, mul vl]\n\t"
        "fmov z14.s, #0.0\n\t" "fmov z15.s, #0.0\n\t"
        "b 5f\n\t"
        "9:\n\t"
        "st1w {z12.s}, p0, [x20]\n\t"
        "st1w {z13.s}, p0, [x20, #1, mul vl]\n\t"
        "fmov z12.s, #0.0\n\t" "fmov z13.s, #0.0\n\t"
        "b 5f\n\t"
        "8:\n\t"
        "st1w {z10.s}, p0, [x20]\n\t"
        "st1w {z11.s}, p0, [x20, #1, mul vl]\n\t"
        "fmov z10.s, #0.0\n\t" "fmov z11.s, #0.0\n\t"
        "b 5f\n\t"
        "30:\n\t"
        "cmp x27, #32\n\t" "b.hs 5f\n\t"
        "cmp x27, #16\n\t" "b.hs 6f\n\t"
        "mov w12, w27\n\t"
        "mova z8.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za1v.s[w12, 0]\n\t"
        "st1w {z8.s}, p0, [x20]\n\t"
        "st1w {z9.s}, p0, [x20, #1, mul vl]\n\t"
        "mova za0v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p0/m, z31.s\n\t"
        "b 5f\n\t"
        "6:\n\t"
        "sub w12, w27, #16\n\t"
        "mova z8.s, p0/m, za2v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za3v.s[w12, 0]\n\t"
        "st1w {z8.s}, p0, [x20]\n\t"
        "st1w {z9.s}, p0, [x20, #1, mul vl]\n\t"
        "mova za2v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za3v.s[w12, 0], p0/m, z31.s\n\t"
        "5:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z4", "z8", "z9", "z10", "z11", "z12", "z13", "z14", "z15", "z24", "z31", "p0", "p3", "memory", "cc");
}

// ---------------- 16×1 单组 + 2 条 fmla 残差：4 tile = 64 列，z16..z19 / z20..z23 为两条 64 列累加链 ----------------
// 每步 4 fmopa + 8 fmla + 2 ld1rw：探针（NOTES fmopa+fmla 并发）证实 16 fmopa + 32 fmla = 32 周期，fmla 免费。
static void k16singlef2(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 1, 640, 63 + P->steps);
    A.n2 = (int64_t)P->kb0; A.e2 = (int64_t)P->kbase; A.T = (int64_t)P->kend; A.nlines = P->cf0;
    A.kb2 = (int64_t)P->kb20; A.cf2 = P->cf20;
    asm volatile(
        LOAD_ARGS
        "ldr x13, [%[A], #184]\n\t"     // kb1 游标
        "ldr x3, [%[A], #248]\n\t"      // kb2 游标（bB 未用）
        "fmov z31.s, #0.0\n\t"
        "fmov z16.s, #0.0\n\t" "fmov z17.s, #0.0\n\t" "fmov z18.s, #0.0\n\t" "fmov z19.s, #0.0\n\t"
        "fmov z20.s, #0.0\n\t" "fmov z21.s, #0.0\n\t" "fmov z22.s, #0.0\n\t" "fmov z23.s, #0.0\n\t"
        "1:\n\t"
        ROW_HEAD_COMMON
        "ldr x21, [%[A], #232]\n\t" "add x21, x9, x21\n\t"
        "prfm pstl2keep, [x21]\n\t" "prfm pstl2keep, [x21, #64]\n\t" "prfm pstl2keep, [x21, #128]\n\t" "prfm pstl2keep, [x21, #192]\n\t"
        "mov x15, x7\n\t"
        ".p2align 4\n"
        "2:\n\t"
        "ld1w {z0.s}, p0/z, [x16]\n\t"
        "ld1w {z1.s}, p0/z, [x16, #1, mul vl]\n\t"
        "ld1w {z2.s}, p0/z, [x16, #2, mul vl]\n\t"
        "ld1w {z3.s}, p0/z, [x16, #3, mul vl]\n\t"
        "ld1w {z4.s}, p0/z, [x2]\n\t"
        "fmopa za0.s, p0/m, p0/m, z0.s, z4.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z1.s, z4.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z2.s, z4.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z3.s, z4.s\n\t"
        "ld1rw {z5.s}, p0/z, [x13]\n\t"
        "ld1rw {z6.s}, p0/z, [x3]\n\t"
        "fmla z16.s, p0/m, z0.s, z5.s\n\t"
        "fmla z17.s, p0/m, z1.s, z5.s\n\t"
        "fmla z18.s, p0/m, z2.s, z5.s\n\t"
        "fmla z19.s, p0/m, z3.s, z5.s\n\t"
        "fmla z20.s, p0/m, z0.s, z6.s\n\t"
        "fmla z21.s, p0/m, z1.s, z6.s\n\t"
        "fmla z22.s, p0/m, z2.s, z6.s\n\t"
        "fmla z23.s, p0/m, z3.s, z6.s\n\t"
        "add x13, x13, #4\n\t"
        "add x3, x3, #4\n\t"
        "add x16, x16, #4\n\t"
        "add x2, x2, #64\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        WRAP_B(x2)
        "ldr x24, [%[A], #208]\n\t"
        "cmp x13, x24\n\t"
        "ldr x22, [%[A], #192]\n\t"
        "csel x13, x22, x13, eq\n\t"
        "cmp x3, x24\n\t"
        "csel x3, x22, x3, eq\n\t"
        SEL_OUT
        // 事件：cA==CF1 → fmla1；cA==CF2 → fmla2；cA<nvA → ZA（三者互斥：CF=20/21 ≥ nvA=16）
        "ldr x24, [%[A], #216]\n\t"
        "cmp x27, x24\n\t" "b.eq 8f\n\t"
        "ldr x24, [%[A], #256]\n\t"
        "cmp x27, x24\n\t" "b.eq 9f\n\t"
        "ldr x24, [%[A], #112]\n\t"
        "cmp x27, x24\n\t" "b.hs 5f\n\t"
        "and w12, w27, #15\n\t"
        "mova z5.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z6.s, p0/m, za1v.s[w12, 0]\n\t"
        "mova z7.s, p0/m, za2v.s[w12, 0]\n\t"
        "mova z8.s, p0/m, za3v.s[w12, 0]\n\t"
        "st1w {z5.s}, p0, [x20]\n\t"
        "st1w {z6.s}, p0, [x20, #1, mul vl]\n\t"
        "st1w {z7.s}, p0, [x20, #2, mul vl]\n\t"
        "st1w {z8.s}, p0, [x20, #3, mul vl]\n\t"
        "mova za0v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za2v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za3v.s[w12, 0], p0/m, z31.s\n\t"
        "b 5f\n\t"
        "8:\n\t"
        "st1w {z16.s}, p0, [x20]\n\t"
        "st1w {z17.s}, p0, [x20, #1, mul vl]\n\t"
        "st1w {z18.s}, p0, [x20, #2, mul vl]\n\t"
        "st1w {z19.s}, p0, [x20, #3, mul vl]\n\t"
        "fmov z16.s, #0.0\n\t" "fmov z17.s, #0.0\n\t" "fmov z18.s, #0.0\n\t" "fmov z19.s, #0.0\n\t"
        "b 5f\n\t"
        "9:\n\t"
        "st1w {z20.s}, p0, [x20]\n\t"
        "st1w {z21.s}, p0, [x20, #1, mul vl]\n\t"
        "st1w {z22.s}, p0, [x20, #2, mul vl]\n\t"
        "st1w {z23.s}, p0, [x20, #3, mul vl]\n\t"
        "fmov z20.s, #0.0\n\t" "fmov z21.s, #0.0\n\t" "fmov z22.s, #0.0\n\t" "fmov z23.s, #0.0\n\t"
        "5:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z4", "z5", "z6", "z7", "z8", "z16", "z17", "z18", "z19", "z20", "z21", "z22", "z23", "z24", "z31", "p0", "p3", "memory", "cc");
}

// ---------------- 8×2：4 tile = 128 列，列 c = 2s+ic；槽 896 B ----------------
static void k8(const kp_t* P)
{
    ka_t A; fill_args(&A, P, 2, 896, 126 + P->steps);
    asm volatile(
        LOAD_ARGS
        "ldr x7, [%[A], #136]\n\t"      // it = steps/2
        "fmov z31.s, #0.0\n\t"
        "1:\n\t"
        ROW_HEAD_COMMON
        // 输出预取：PD 行后是否有事件（(cA+PD) mod KH < nv）
        "ldr x23, [%[A], #144]\n\t"
        "add x22, x27, x23\n\t" "cmp x22, x6\n\t" "sub x21, x22, x6\n\t" "csel x22, x21, x22, hs\n\t"
        "cmp x22, x24\n\t" "b.hs 6f\n\t"
        "ldr x21, [%[A], #232]\n\t" "add x21, x9, x21\n\t"
        "prfm pstl2keep, [x21]\n\t" "prfm pstl2keep, [x21, #64]\n\t" "prfm pstl2keep, [x21, #128]\n\t" "prfm pstl2keep, [x21, #192]\n\t"
        "prfm pstl2keep, [x21, #256]\n\t" "prfm pstl2keep, [x21, #320]\n\t" "prfm pstl2keep, [x21, #384]\n\t" "prfm pstl2keep, [x21, #448]\n\t"
        "6:\n\t"
        "mov x15, x7\n\t"
        "2:\n\t"
        "ld2w {z0.s, z1.s}, p0/z, [x16]\n\t"
        "ld2w {z2.s, z3.s}, p0/z, [x16, #2, mul vl]\n\t"
        "ld2w {z4.s, z5.s}, p0/z, [x16, #4, mul vl]\n\t"
        "ld2w {z6.s, z7.s}, p0/z, [x16, #6, mul vl]\n\t"
        "ld1w {z8.s}, p0/z, [x2]\n\t"
        "ld1w {z9.s}, p0/z, [x2, #1, mul vl]\n\t"
        "fmopa za0.s, p0/m, p0/m, z0.s, z8.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z2.s, z8.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z4.s, z8.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z6.s, z8.s\n\t"
        "fmopa za0.s, p0/m, p0/m, z1.s, z9.s\n\t"
        "fmopa za1.s, p0/m, p0/m, z3.s, z9.s\n\t"
        "fmopa za2.s, p0/m, p0/m, z5.s, z9.s\n\t"
        "fmopa za3.s, p0/m, p0/m, z7.s, z9.s\n\t"
        "add x16, x16, #8\n\t"
        "add x2, x2, #128\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        WRAP_B(x2) SEL_OUT
        "cmp x27, x24\n\t" "b.hs 4f\n\t"
        "and w12, w27, #7\n\t" "lsl w12, w12, #1\n\t"
        "mova z8.s, p0/m, za0v.s[w12, 0]\n\t"
        "mova z9.s, p0/m, za0v.s[w12, 1]\n\t"
        "mova z10.s, p0/m, za1v.s[w12, 0]\n\t"
        "mova z11.s, p0/m, za1v.s[w12, 1]\n\t"
        "mova z12.s, p0/m, za2v.s[w12, 0]\n\t"
        "mova z13.s, p0/m, za2v.s[w12, 1]\n\t"
        "mova z14.s, p0/m, za3v.s[w12, 0]\n\t"
        "mova z15.s, p0/m, za3v.s[w12, 1]\n\t"
        "st2w {z8.s, z9.s}, p0, [x20]\n\t"
        "st2w {z10.s, z11.s}, p0, [x20, #2, mul vl]\n\t"
        "st2w {z12.s, z13.s}, p0, [x20, #4, mul vl]\n\t"
        "st2w {z14.s, z15.s}, p0, [x20, #6, mul vl]\n\t"
        "mova za0v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za0v.s[w12, 1], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za1v.s[w12, 1], p0/m, z31.s\n\t"
        "mova za2v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za2v.s[w12, 1], p0/m, z31.s\n\t"
        "mova za3v.s[w12, 0], p0/m, z31.s\n\t"
        "mova za3v.s[w12, 1], p0/m, z31.s\n\t"
        "4:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z4", "z5", "z6", "z7", "z8", "z9", "z10", "z11", "z12", "z13", "z14", "z15", "z24", "z31", "p0", "p3", "memory", "cc");
}

// ---------------- 4×4：≤4 个残差 × 4 个 X 偏移；4 tile 横排 = 256 列；步数 pad 到 4 的倍数（多出的步 b=0，fma(a,0,acc) 位不变）----------------
// 列 c = 4s+ic：残差 s_base+s 的输出列 i = base + 64t + 4r + ic。a_t(X)[r] = row[base+64t+4r+X] = plane_{X&3}[(X>>2)+16t+r]，
// planes 由单级 ld4w 去交织得到（stride 4，与经典内核同构）；事件时 mova 4 竖切片 + st4w 交织出 64 个连续 float（同经典抽取）。
#define K4_CP(DST) /* 源 x22 → 槽 DST 的 4 个平面（距 x3）；预取游标 x21；用 x12 x13 x23 x24 */ \
        "mov x12, x22\n\t" "mov x13, " #DST "\n\t" \
        "ldr x24, [%[A], #168]\n\t" \
        "cbz x24, 11f\n\t" \
        "10:\n\t" \
        "prfm pldl2keep, [x21]\n\t" "prfm pldl2keep, [x21, #64]\n\t" "prfm pldl2keep, [x21, #128]\n\t" "prfm pldl2keep, [x21, #192]\n\t" \
        "ld4w {z0.s, z1.s, z2.s, z3.s}, p0/z, [x12]\n\t" \
        "st1w {z0.s}, p0, [x13]\n\t" "add x23, x13, x3\n\t" "st1w {z1.s}, p0, [x23]\n\t" \
        "add x23, x23, x3\n\t" "st1w {z2.s}, p0, [x23]\n\t" "add x23, x23, x3\n\t" "st1w {z3.s}, p0, [x23]\n\t" \
        "add x12, x12, #256\n\t" "add x13, x13, #64\n\t" "add x21, x21, #256\n\t" "subs x24, x24, #1\n\t" "b.ne 10b\n\t" \
        "11:\n\t" \
        "prfm pldl2keep, [x21]\n\t" "prfm pldl2keep, [x21, #64]\n\t" "prfm pldl2keep, [x21, #128]\n\t" "prfm pldl2keep, [x21, #192]\n\t" \
        "ldr x24, [%[A], #176]\n\t" \
        "whilelo p4.s, xzr, x24\n\t" \
        "ld4w {z0.s, z1.s, z2.s, z3.s}, p4/z, [x12]\n\t" \
        "st1w {z0.s}, p4, [x13]\n\t" "add x23, x13, x3\n\t" "st1w {z1.s}, p4, [x23]\n\t" \
        "add x23, x23, x3\n\t" "st1w {z2.s}, p4, [x23]\n\t" "add x23, x23, x3\n\t" "st1w {z3.s}, p4, [x23]\n\t" \
        "ldr x24, [%[A], #112]\n\t"
#define K4_STEP(PQ, BOFF) \
        "ld1w {z0.s}, p0/z, [" #PQ "]\n\t" \
        "ld1w {z1.s}, p0/z, [" #PQ ", #1, mul vl]\n\t" \
        "ld1w {z2.s}, p0/z, [" #PQ ", #2, mul vl]\n\t" \
        "ld1w {z3.s}, p0/z, [" #PQ ", #3, mul vl]\n\t" \
        "ld1w {z4.s}, p0/z, [x2, #" #BOFF ", mul vl]\n\t" \
        "fmopa za0.s, p0/m, p0/m, z0.s, z4.s\n\t" \
        "fmopa za1.s, p0/m, p0/m, z1.s, z4.s\n\t" \
        "fmopa za2.s, p0/m, p0/m, z2.s, z4.s\n\t" \
        "fmopa za3.s, p0/m, p0/m, z3.s, z4.s\n\t"
#define K4_EV(T) \
        "mova z0.s, p0/m, za" #T "v.s[w12, 0]\n\t" \
        "mova z1.s, p0/m, za" #T "v.s[w12, 1]\n\t" \
        "mova z2.s, p0/m, za" #T "v.s[w12, 2]\n\t" \
        "mova z3.s, p0/m, za" #T "v.s[w12, 3]\n\t" \
        "st4w {z0.s, z1.s, z2.s, z3.s}, p0, [x20, #4*" #T ", mul vl]\n\t" \
        "mova za" #T "v.s[w12, 0], p0/m, z31.s\n\t" \
        "mova za" #T "v.s[w12, 1], p0/m, z31.s\n\t" \
        "mova za" #T "v.s[w12, 2], p0/m, z31.s\n\t" \
        "mova za" #T "v.s[w12, 3], p0/m, z31.s\n\t"
static void k4(const kp_t* P)
{
    const long steps4 = P->steps;                                  // 已 pad 到 4 的倍数
    const long sh = ((uintptr_t)P->in_row >> 2) & 15;              // 对齐拷贝源到 64 B；平面起点相应排列
    const long ncp = steps4 + 252 + sh;                            // a 跨度：192 + 60 + (steps4-1) + 1 + 偏移
    const long TSB = (((ncp + 3) / 4 + 15) & ~15L) * 4;            // 平面距（字节）
    ka_t A; fill_args(&A, P, 1, 0, 0);
    A.in_row = (int64_t)(P->in_row - sh);
    A.slot = 4 * TSB;
    A.it = (P->KW + 3) / 4;
    A.kw4 = (P->KW + 3) % 4;
    A.ncp_full = ncp / 64; A.ncp_tail = ((ncp % 64) + 3) / 4;      // ld4w 整块数、尾块每平面元素数
    A.TSB = TSB;
    A.n2 = TSB * ((sh + 0) & 3) + 4 * ((sh + 0) >> 2);             // 子步 i 的平面起点偏移（相对槽基址）
    A.e2 = TSB * ((sh + 1) & 3) + 4 * ((sh + 1) >> 2);
    A.T  = TSB * ((sh + 2) & 3) + 4 * ((sh + 2) >> 2);
    A.nlines = TSB * ((sh + 3) & 3) + 4 * ((sh + 3) >> 2);
    asm volatile(
        LOAD_ARGS
        "ldr x3, [%[A], #200]\n\t"      // TSB（覆盖 bB）
        "ldr x7, [%[A], #136]\n\t"      // it = steps4/4
        "fmov z31.s, #0.0\n\t"
        // 序言：行 0 → 槽 0
        "mov x22, x0\n\t"
        "add x21, x0, x26\n\t"
        K4_CP(x17)
        "1:\n\t"
        // 换槽 + 拷下一行（末行时拷本行）
        "mov x16, x17\n\t"
        "sub x17, x28, x17\n\t"
        "add x22, x0, x1\n\t" "cmp x8, #1\n\t" "csel x22, x0, x22, eq\n\t"
        "add x21, x0, x26\n\t"
        K4_CP(x17)
        // 平面指针 p0..p3 = x16, x22, x23, x25（起点按 sh 排列）
        "ldr x22, [%[A], #192]\n\t" "add x22, x22, x16\n\t"
        "ldr x23, [%[A], #208]\n\t" "add x23, x23, x16\n\t"
        "ldr x25, [%[A], #216]\n\t" "add x25, x25, x16\n\t"
        "ldr x12, [%[A], #184]\n\t" "add x16, x16, x12\n\t"
        "mov x15, x7\n\t"
        "2:\n\t"
        K4_STEP(x16, 0)
        K4_STEP(x22, 1)
        K4_STEP(x23, 2)
        K4_STEP(x25, 3)
        "add x16, x16, #4\n\t"
        "add x22, x22, #4\n\t"
        "add x23, x23, #4\n\t"
        "add x25, x25, #4\n\t"
        "add x2, x2, #256\n\t"
        "subs x15, x15, #1\n\t"
        "b.ne 2b\n\t"
        "ldr x12, [%[A], #264]\n\t"
        "cbz x12, 42f\n\t"
        K4_STEP(x16, 0)
        "cmp x12, #1\n\t" "b.eq 41f\n\t"
        K4_STEP(x22, 1)
        "cmp x12, #2\n\t" "b.eq 41f\n\t"
        K4_STEP(x23, 2)
        "41:\n\t" "add x2, x2, #256\n\t"
        "42:\n\t"
        WRAP_B(x2) SEL_OUT
        "cmp x27, x24\n\t" "b.hs 4f\n\t"
        "lsl w12, w27, #2\n\t"
        K4_EV(0)
        K4_EV(1)
        K4_EV(2)
        K4_EV(3)
        "4:\n\t"
        ADV_CNT(x27)
        ROW_TAIL
        :
        : [A]"r"(&A)
        : XCLOB, "z0", "z1", "z2", "z3", "z4", "z31", "p0", "p3", "p4", "memory", "cc");
}
// b 表：kind 16: R[y][X][c] = k[(y-c) mod KH][X]（残差 s_base+c ≥ KH → 0）；kind 8: c=2s+ic → k[(y-s) mod KH][X-ic]；kind 4: c=4s+ic
static void roll_build_R(float* R, const float* k, long KH, long KW, long steps, long s_base, int kind)
{
    for (long y = 0; y < KH; y++)
        for (long X = 0; X < steps; X++)
            for (long c = 0; c < 16; c++) {
                long sidx, ic;
                if (kind == 16) { sidx = c; ic = 0; } else if (kind == 8) { sidx = c >> 1; ic = c & 1; } else { sidx = c >> 2; ic = c & 3; }
                long ki = X - ic, kj = ((y - sidx) % KH + KH) % KH;
                R[(y * steps + X) * 16 + c] = (ki >= 0 && ki < KW && s_base + sidx < KH) ? k[kj * KW + ki] : 0.f;
            }
}
typedef struct { int kind; long s_base, nvA, nvB, width, steps, RSB; float* R; size_t Rcap; float* kf; size_t kfcap; } rgrp_t;   // kind 32=pair,16=single,8,4; 33/34=pair+fmla；kf = pairf3 的三链 b 打包 [KH][steps][4]
typedef struct { int g; long base; } ritem_t;
typedef struct { int item; long ja, jb; } rpiece_t;
typedef struct {
    rgrp_t G[12]; int ng;
    ritem_t* items; double* cost; int nit, itcap; double C;
    rpiece_t* pieces; int* pstart; int npieces, pcap, pnth;      // 静态划分：线程 t 的片段 pieces[pstart[t] .. pstart[t+1])
    float* rings; float* scratch; int nthr_alloc;
    float* kcopy; size_t kcopy_n; long KH, KW, outW, outH;
} rplan_t;
static rplan_t g_rp;
static padded_u64 g_rwork[1024] __attribute__((aligned(64)));   // 每线程片段游标 (end<<32 | cur)，CAS 认领 + 空了从别人尾部偷
static int g_roll_diag = 0;
typedef struct { uint64_t tk[4]; long ts[4]; uint64_t tot; } rdiag_t;   // 每线程：各类内核的 cntvct 计时与 tile-步数
static rdiag_t g_rdiag[1024];
static inline int roll_kind_idx(int kind) { return (kind == 32 || kind == 33 || kind == 34 || kind == 35) ? 0 : (kind == 16 || kind == 17) ? 1 : kind == 8 ? 2 : 3; }

// 分组：16 组成对；单 16；余 ≥3 → 8×2（≤8 个）；余 1–2 → 每个残差一个 1×16
static int roll_groups(long KH, long KW, rgrp_t* G)
{
    int ng = 0; long s = 0, n16 = KH / 16, rem = KH - n16 * 16;
    int npair = (int)(n16 / 2);
    // rem == 9 或 1 且有 pair 组：最后一个 pair 升级为 pair+fmla（kind 33，第 33 个残差 = KH-1，
    // 用 fmopa 旁的免费 fmla 累加），余数变 8/0 → 8×2 满槽 / 无 K4（k41: 32+8+1 → 33+8；k81: 64+16+1 → 65+16）
    int fmla = (npair >= 1 && (rem == 9 || rem == 1)) ? 1 : 0;   // pair+1fmla：k41(32+8+1→33+8)、k81(64+16+1→65+16)
    int nf = (npair >= 1 && rem == 7) ? ((n16 & 1) ? 3 : 4) : 0;   // pair+3/4fmla 消掉 8×2；无 single16 组（n16 偶）时用 4 链更快（k39），有则 3 链（k55），同节点 A/B 实测
    int pk = nf == 4 ? 35 : 34;
    for (int i = 0; i < npair; i++) { G[ng++] = (rgrp_t){(i == npair - 1 && nf) ? pk : (i == npair - 1 && fmla) ? 33 : 32, s, 16, 16, 32, KW, 0, NULL, 0}; s += 32; }
    if (n16 & 1) { G[ng++] = (rgrp_t){16, s, 16, 0, 64, KW, 0, NULL, 0}; s += 16; }
    if (fmla) rem -= 1;
    rem -= nf;
    while (rem >= 5) { long nv = rem > 8 ? 8 : rem; G[ng++] = (rgrp_t){8, s, nv, 0, 128, (KW & 1) ? KW + 1 : KW + 2, 0, NULL, 0}; s += nv; rem -= nv; }
    if (rem > 0) { G[ng++] = (rgrp_t){4, s, rem, 0, 256, (KW + 3 + 3) & ~3L, 0, NULL, 0}; s += rem; rem = 0; }
    for (int g = 0; g < ng; g++) G[g].RSB = G[g].steps * 64;
    return ng;
}
// 形状是否适合滚动形态：KW 奇数（8×2 的步数 KW+1 为偶数且末条带读不越界）、最宽组的条带放得下、行数足够
static int roll_shape_ok(long H, long W, long KH, long KW)
{
    if (KH < 16 || KW < 3 || KW > 400) return 0;
    rgrp_t G[12]; int ng = roll_groups(KH, KW, G);
    long outW = W - KW + 1, outH = H - KH + 1;
    for (int g = 0; g < ng; g++) if (outW < G[g].width) return 0;
    if (outH < 1) return 0;
    return 1;
}
static int roll_auto(long H, long W, long KH, long KW)
{
    (void)H; (void)W;
    return (KH == 39 && KW == 39) || (KH == 41 && KW == 41) || (KH == 55 && KW == 55) || (KH == 81 && KW == 81);   // 四例全滚动：pair+fmla（1/3 条链）消掉余数组
}

static void roll_prepare(const float* k, long H, long W, long KH, long KW, int nth)
{
    rplan_t* P = &g_rp;
    const long outW = W - KW + 1, outH = H - KH + 1;
    const size_t kn = (size_t)KH * KW;
    int same = P->kcopy && P->kcopy_n >= kn && P->KH == KH && P->KW == KW && P->outW == outW && memcmp(P->kcopy, k, kn * 4) == 0;
    if (!same) {
        rgrp_t groups[12];
        P->ng = roll_groups(KH, KW, groups);
        for (int g = 0; g < P->ng; g++) {
            groups[g].R = P->G[g].R; groups[g].Rcap = P->G[g].Rcap;
            groups[g].kf = P->G[g].kf; groups[g].kfcap = P->G[g].kfcap;
            P->G[g] = groups[g];
        }
        for (int g = 0; g < P->ng; g++) {
            rgrp_t* G = &P->G[g];
            size_t need = (size_t)KH * G->RSB;
            if (G->Rcap < need) { free(G->R); G->R = alloc_aligned(need); G->Rcap = G->R ? need : 0; }
            roll_build_R(G->R, k, KH, KW, G->steps, G->s_base, (G->kind == 32 || G->kind == 33 || G->kind == 34 || G->kind == 35 || G->kind == 17) ? 16 : G->kind);
            if (G->kind == 34 || G->kind == 35) {
                size_t kfneed = (size_t)KH * G->steps * 4 * sizeof(float);
                if (G->kfcap < kfneed) { free(G->kf); G->kf = alloc_aligned(kfneed); G->kfcap = G->kf ? kfneed : 0; }
                for (long a = 0; a < KH; a++)               // kf[a][X] = {k[a][X], k[(a+1)%KH][X], k[(a+2)%KH][X], 0}
                    for (long X = 0; X < G->steps; X++) {
                        float* d = G->kf + (a * G->steps + X) * 4;
                        d[0] = X < KW ? k[a * KW + X] : 0.f;
                        d[1] = X < KW ? k[((a + 1) % KH) * KW + X] : 0.f;
                        d[2] = X < KW ? k[((a + 2) % KH) * KW + X] : 0.f;
                        d[3] = (G->kind == 35 && X < KW) ? k[((a + 3) % KH) * KW + X] : 0.f;
                    }
            }
        }
        int nit = 0;
        for (int g = 0; g < P->ng; g++) nit += (int)((outW + P->G[g].width - 1) / P->G[g].width);
        if (P->itcap < nit) { free(P->items); free(P->cost); P->items = malloc(nit * sizeof(ritem_t)); P->cost = malloc(nit * sizeof(double)); P->itcap = nit; }
        P->nit = 0; P->C = 0;
        for (int g = 0; g < P->ng; g++) {
            const rgrp_t* G = &P->G[g];
            long nstrip = (outW + G->width - 1) / G->width;
            for (long st = 0; st < nstrip; st++) {
                long base = st * G->width; if (base + G->width > outW) base = outW - G->width;
                P->items[P->nit] = (ritem_t){g, base};
                double w = G->kind == 8 ? env_int("CONV_ROLL_W8", 104) / 100.0 : G->kind == 4 ? env_int("CONV_ROLL_W4", 123) / 100.0 : (G->kind == 16 || G->kind == 17) ? env_int("CONV_ROLL_W16", 102) / 100.0 : 1.0;
                P->cost[P->nit] = (double)G->steps * outH * w;   // ∝ tile-步数（各类都是 4 tile）× 相对慢速权重
                P->C += P->cost[P->nit]; P->nit++;
            }
        }
        if (P->kcopy_n < kn) { free(P->kcopy); P->kcopy = malloc(kn * 4); P->kcopy_n = P->kcopy ? kn : 0; }
        if (P->kcopy) memcpy(P->kcopy, k, kn * 4);
        P->KH = KH; P->KW = KW; P->outW = outW;
    }
    if (!same || P->pnth != nth || P->outH != outH) {
        // 精确静态划分：片段代价 = 权重 × 步数 × (行数 + KH-1)，贪心填到目标，整项放不下就按行切开
        const long ovh = KH - 1;
        int need = 2 * P->nit + 2 * nth + 4;
        if (P->pcap < need) { free(P->pieces); free(P->pstart); P->pieces = malloc(need * sizeof(rpiece_t)); P->pstart = malloc((nth + 1) * sizeof(int)); P->pcap = need; }
        double total = 0, wsum = 0;
        for (int i = 0; i < P->nit; i++) { double w = P->cost[i] / outH; total += w * (outH + ovh); wsum += w; }
        total += (nth - 1) * (wsum / P->nit) * ovh;
        const double target = total / nth;
        int np = 0, i = 0; long r = 0;
        for (int t = 0; t < nth; t++) {
            P->pstart[t] = np; double acc = 0;
            while (i < P->nit) {
                double w = P->cost[i] / outH; long R = outH - r;
                double full = w * (R + ovh);
                if (acc + full <= target * 1.0005 || t == nth - 1) { P->pieces[np++] = (rpiece_t){i, r, outH}; acc += full; i++; r = 0; continue; }
                long rows = (long)((target - acc) / w) - ovh;
                if (rows < 8) break;
                if (rows > R - 8) rows = R - 8;                // 剩余太少就整项给下一个线程
                P->pieces[np++] = (rpiece_t){i, r, r + rows}; acc += w * (rows + ovh); r += rows;
                break;
            }
        }
        P->pstart[nth] = np; P->npieces = np; P->pnth = nth; P->outH = outH;
    }
    if (P->nthr_alloc < nth) {
        free(P->rings); free(P->scratch);
        P->rings = alloc_aligned((size_t)nth * 32768); P->scratch = alloc_aligned((size_t)nth * 8192);
        P->nthr_alloc = nth;
    }
}

static void roll_worker(int tid, int nth, const ctx_t* c)
{
    const rplan_t* P = (const rplan_t*)c->rp;
    const long KH = c->KH, KW = c->KW, W = c->W;
    float* ring = P->rings + (size_t)tid * 8192; float* scr = P->scratch + (size_t)tid * 2048;
    rdiag_t* D = &g_rdiag[tid]; uint64_t t_start = 0;
    if (g_roll_diag) { memset(D, 0, sizeof(*D)); t_start = cyc(); }
    if (tid >= nth || tid >= P->pnth) return;
    sme_start();
    int victim = tid;
    for (;;) {
        // 认领：先取自己的下一片；空了就从"剩得最多"的线程尾部偷一片（relaxed CAS，与经典内核同理）
        int pi = -1;
        for (;;) {
            uint64_t w = __atomic_load_n(&g_rwork[victim].v, __ATOMIC_RELAXED);
            uint32_t cur = (uint32_t)w, end = (uint32_t)(w >> 32);
            if (cur >= end) break;
            uint64_t nw = (victim == tid) ? w + 1 : w - ((uint64_t)1 << 32);
            if (__atomic_compare_exchange_n(&g_rwork[victim].v, &w, nw, 1, __ATOMIC_RELAXED, __ATOMIC_RELAXED)) { pi = (victim == tid) ? (int)cur : (int)end - 1; break; }
        }
        if (pi < 0) {
            if (victim == tid) {
                int best = -1; uint32_t most = 0;
                for (int t = 0; t < nth; t++) {
                    uint64_t w = __atomic_load_n(&g_rwork[t].v, __ATOMIC_RELAXED);
                    uint32_t rem = (uint32_t)(w >> 32) - (uint32_t)w;
                    if ((int32_t)rem > 0 && rem > most) { most = rem; best = t; }
                }
                if (best < 0) break;
                victim = best; continue;
            }
            victim = tid; continue;                       // 偷失败/偷空了：回自己再扫一遍
        }
        const rpiece_t* pc = &P->pieces[pi];
        const long ja = pc->ja, jb = pc->jb;
        const rgrp_t* g = &P->G[P->items[pc->item].g];
        const long base = P->items[pc->item].base;
        uint64_t t0 = g_roll_diag ? cyc() : 0;
        kp_t K = { c->in + ja * W + base, W * 4, g->R, g->RSB, KH, g->steps, jb - ja + KH - 1,
                   c->out + (ja - KH + 1) * c->outW + base, scr,
                   ((ja + 1 - g->s_base) % KH + KH) % KH, ((ja + 1 - g->s_base - 16) % KH + KH) % KH,
                   ((ja - g->s_base) % KH + KH) % KH, ((ja - g->s_base - 16) % KH + KH) % KH, g->nvA, g->nvB, ring, KW, c->outW * 4,
                   NULL, NULL, NULL, 0, NULL, 0 };
        if (g->kind == 34 || g->kind == 35) {
            const long sF = KH - 1, a0 = ((ja - sF) % KH + KH) % KH;   // kf 链的起始 kernel 行
            K.kb0 = g->kf + a0 * g->steps * 4; K.kbase = g->kf; K.kend = g->kf + KH * g->steps * 4;
            K.cf0 = ((sF - g->s_base) % KH + KH) % KH;
        } else if (g->kind == 33) {
            const long sF = KH - 1, kj0 = ((ja - sF) % KH + KH) % KH;
            K.kb0 = c->k + kj0 * KW; K.kbase = c->k; K.kend = c->k + KH * KW;
            K.cf0 = ((sF - g->s_base) % KH + KH) % KH;
        } else if (g->kind == 17) {
            const long sF1 = KH - 3, sF2 = KH - 2;
            K.kb0 = c->k + (((ja - sF1) % KH + KH) % KH) * KW;
            K.kb20 = c->k + (((ja - sF2) % KH + KH) % KH) * KW;
            K.kbase = c->k; K.kend = c->k + KH * KW;
            K.cf0 = ((sF1 - g->s_base) % KH + KH) % KH;
            K.cf20 = ((sF2 - g->s_base) % KH + KH) % KH;
        }
        sme_zero_za();
        if (g->kind == 32) k16pair(&K); else if (g->kind == 33) k16pairf(&K); else if (g->kind == 34) k16pairf3(&K); else if (g->kind == 35) k16pairf4(&K); else if (g->kind == 16) k16single(&K);
        else if (g->kind == 17) k16singlef2(&K); else if (g->kind == 8) k8(&K); else k4(&K);
        if (g_roll_diag) { int ki = roll_kind_idx(g->kind); D->tk[ki] += cyc() - t0; D->ts[ki] += 4L * g->steps * (jb - ja + KH - 1); }
    }
    sme_stop();
    if (g_roll_diag) D->tot = cyc() - t_start;
}
static void roll_diag_print(int nth)
{
    const double tick_cyc = 1.55e9 / 1e8;    // cntvct 100 MHz → 1.55 GHz 周期
    uint64_t tk[4] = {0}; long ts[4] = {0}; double mn = 1e9, mx = 0, av = 0;
    for (int t = 0; t < nth; t++) {
        for (int k = 0; k < 4; k++) { tk[k] += g_rdiag[t].tk[k]; ts[k] += g_rdiag[t].ts[k]; }
        double ms = g_rdiag[t].tot / 1e5; if (ms < mn) mn = ms; if (ms > mx) mx = ms; av += ms / nth;
    }
    fprintf(stderr, "[roll] thr ms min/avg/max %.3f/%.3f/%.3f | 周期/tile步: pair %.2f single %.2f 8x2 %.2f 4x4 %.2f | 份额 %%: %.1f %.1f %.1f %.1f\n", mn, av, mx,
            ts[0] ? tk[0] * tick_cyc / ts[0] : 0, ts[1] ? tk[1] * tick_cyc / ts[1] : 0, ts[2] ? tk[2] * tick_cyc / ts[2] : 0, ts[3] ? tk[3] * tick_cyc / ts[3] : 0,
            100.0 * tk[0] / (tk[0] + tk[1] + tk[2] + tk[3] + 1), 100.0 * tk[1] / (tk[0] + tk[1] + tk[2] + tk[3] + 1), 100.0 * tk[2] / (tk[0] + tk[1] + tk[2] + tk[3] + 1), 100.0 * tk[3] / (tk[0] + tk[1] + tk[2] + tk[3] + 1));
    if (getenv("CONV_ROLL_DIAG_THR")) {
        for (int t = 0; t < nth; t++) {
            uint64_t tks = g_rdiag[t].tk[0] + g_rdiag[t].tk[1] + g_rdiag[t].tk[2] + g_rdiag[t].tk[3];
            long tss = g_rdiag[t].ts[0] + g_rdiag[t].ts[1] + g_rdiag[t].ts[2] + g_rdiag[t].ts[3];
            fprintf(stderr, " %d:%.2f/%.1fM/%.2f", t, g_rdiag[t].tot / 1e5, tss / 1e6, tss ? tks * tick_cyc / tss : 0);   // 总ms/百万tile步/周期每步
        }
        fprintf(stderr, "\n");
    }
}

static void conv_worker_diag(int tid, int nt_, const ctx_t* c)
{
    if (c->mode == 1) { roll_worker(tid, nt_, c); return; }
    if (!g_diag_on) { conv_worker(tid, nt_, c); return; }
    diag_t* dg = &g_diag[tid];
    dg->ghz0 = dg->fmopa_ns = 0;
    if (c->call_id == 2) {
        char* dbuf = mmap(NULL, DIAG_BW_BYTES, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (dbuf == MAP_FAILED) dbuf = NULL; else memset(dbuf, 1, DIAG_BW_BYTES);
        sme_start();
        diag_ghz(256); dg->ghz0 = diag_ghz(4096); diag_fmopa_ns(2000); dg->fmopa_ns = diag_fmopa_ns(20000);
        diag_barrier(nt_, 1);                          // 全部核同时做 ~15 ms 的 fmopa 满载，再测主频：功耗降频在这里现形
        dg->fmopa_ns2 = diag_fmopa_ns(1500000);
        diag_ghz(256); dg->ghz_fm = diag_ghz(2048);
        // 只有一半 / 四分之一的核满载时的 fmopa 速率与主频：若评测机按活跃核数提频，少线程可能反而更快
        dg->fm_half = dg->fm_quarter = dg->ghz_half = 0;
        diag_barrier(nt_, 2);
        if (tid < nt_ / 2) { dg->fm_half = diag_fmopa_ns(1500000); diag_ghz(256); dg->ghz_half = diag_ghz(2048); }
        diag_barrier(nt_, 3);
        if (tid < nt_ / 4) dg->fm_quarter = diag_fmopa_ns(1500000);
        diag_bw(nt_, dg, dbuf);
        sme_stop();
        if (dbuf) munmap(dbuf, DIAG_BW_BYTES);
    }
    dg->c0 = cyc();
    conv_worker(tid, nt_, c);
    dg->c1 = cyc();
    diag_ghz(256); dg->ghz1 = diag_ghz(2048);   // 负载下主频（其他线程多半还在算）：先热身（冷链路 ~4% 偏低），再 16384 周期 ≈ 10 µs
}

// ---------------------------------------------------------------- 自有线程池（可选）：调用之间自旋等待，省去 OpenMP 唤醒 ~0.1–0.2 ms
#include <pthread.h>
// 每线程一条 go 线：37 个线程同时自旋读同一条线时，主线程对它的原子 RMW 要等所有共享者失效，
// 实测各线程进入偏差 30–45 µs（case1 的 0.5–0.7%）；改为主线程依次写各线程私有的 go 线（无共享争用）
static padded_u64 g_go_t[1024] __attribute__((aligned(64)));
static padded_u64 g_done __attribute__((aligned(64)));
static uint64_t g_go_gen = 0;
static uint64_t g_prof_c_go = 0, g_prof_c_go2 = 0;   // 分相：主线程发 go 前/后的时间戳
static const ctx_t* volatile g_pool_ctx;
static int g_pool_nth = 0;      // 池线程数（含主线程）；0 = 未建立
static int g_main_pinned = 0;
static pthread_t g_pool_thr[1024];

static int g_pool_wfe = 0;      // 1: 用 ldaxr+wfe 等待（主线程 sev 唤醒）；0: 纯自旋
static void* pool_worker(void* arg)
{
    const int tid = (int)(intptr_t)arg;
    pin_self(tid);
    uint64_t seen = 0;
    volatile uint64_t* go = &g_go_t[tid].v;
    for (;;) {
        uint64_t g;
        if (g_pool_wfe) {
            for (;;) {
                asm volatile("ldaxr %0, [%1]" : "=r"(g) : "r"(go) : "memory");
                if (g != seen) break;
                asm volatile("wfe" ::: "memory");
            }
        } else {
            while ((g = __atomic_load_n(go, __ATOMIC_ACQUIRE)) == seen) asm volatile("yield" ::: "memory");
        }
        seen = g;
        conv_worker_diag(tid, g_pool_nth, g_pool_ctx);
        __atomic_fetch_add(&g_done.v, 1, __ATOMIC_ACQ_REL);
    }
    return NULL;
}

static int pool_start(int nth)
{
    if (g_pool_nth == nth) return 1;
    if (g_pool_nth != 0) return 0;               // 线程数变化：不重建，回退 OpenMP
    for (int t = 1; t < nth; t++) {
        if (pthread_create(&g_pool_thr[t], NULL, pool_worker, (void*)(intptr_t)t) != 0) { g_pool_nth = -1; return 0; }
    }
    g_pool_nth = nth;
    return 1;
}

static void run_parallel(int nth, const ctx_t* c, int use_pool)
{
    if (use_pool && nth > 1 && nth <= 1024 && pool_start(nth)) {
        ((ctx_t*)c)->pool = 1;
        g_pool_ctx = c;
        __atomic_store_n(&g_done.v, 0, __ATOMIC_RELEASE);
        const uint64_t gen = ++g_go_gen;
        if (c->prof) g_prof_c_go = cyc();
        for (int t = 1; t < nth; t++) __atomic_store_n(&g_go_t[t].v, gen, __ATOMIC_RELEASE);
        if (c->prof) g_prof_c_go2 = cyc();
        if (g_pool_wfe) asm volatile("sev" ::: "memory");
        if (!g_main_pinned) { pin_self(0); g_main_pinned = 1; }
        conv_worker_diag(0, nth, c);
        while (__atomic_load_n(&g_done.v, __ATOMIC_ACQUIRE) != (uint64_t)(nth - 1)) asm volatile("yield" ::: "memory");
        return;
    }
#pragma omp parallel num_threads(nth)
    {
        conv_worker_diag(omp_get_thread_num(), omp_get_num_threads(), c);
    }
}

static void conv2d_roll(const CONVFLOAT* in, CONVINT H, CONVINT W, const CONVFLOAT* k, CONVINT KH, CONVINT KW,
                        CONVFLOAT* out, int nth)
{
    read_knobs();
    g_roll_pd = g_knobs.roll_pd;
    g_roll_diag = env_int("CONV_ROLL_DIAG", 0);
    roll_prepare(k, H, W, KH, KW, nth);
    ctx_t ctx; memset(&ctx, 0, sizeof(ctx));
    ctx.in = in; ctx.k = k; ctx.out = out; ctx.H = H; ctx.W = W; ctx.KH = KH; ctx.KW = KW; ctx.outH = H - KH + 1; ctx.outW = W - KW + 1;
    ctx.mode = 1; ctx.rp = &g_rp;
    for (int t = 0; t < nth; t++) g_rwork[t].v = ((uint64_t)g_rp.pstart[t + 1] << 32) | (uint32_t)g_rp.pstart[t];
    run_parallel(nth, &ctx, g_knobs.pool);
    if (g_roll_diag) roll_diag_print(nth);
}

static void conv2d_sme(const CONVFLOAT* in, CONVINT H, CONVINT W, const CONVFLOAT* k, CONVINT KH, CONVINT KW,
                       CONVFLOAT* out, int nth)
{
    const long outH = H - KH + 1, outW = W - KW + 1;
    const double t_entry = omp_get_wtime();
    // 块宽 256*SP：SP=2 时每个输入行只需去交织一次即可服务 512 列（构建开销减半），但环形缓冲翻倍；
    // 自动规则：环形缓冲(SP=2) + 打包 kernel 能放进 ~400 KB L2 预算时取 2，否则 1（可用 CONV_SP 覆盖）
    read_knobs();
    const int slice_ovl = g_knobs.slice;              // 下一组的平面构建以 ld4w 切片形式穿插进 pass 的 asm 行循环
    int SP = g_knobs.sp;
    if (SP <= 0) {
        // 自动规则：取满足 (a) 环形缓冲 + 打包 kernel ≤ ~400 KB L2 预算，(b) 切片构建能在一个 pass 内完成
        //（每行 ceil((m4-1)/16) 片，需 chunks + 4*PW/16 ≤ (KH+3)*chunks）的最大 SP
        const long m4a = (KW + 3) / 4;
        const long chunks = (m4a + 14) / 16;
        const long rbytes = (KH + 4) * pow2_stride(16L * (KW + 6));
        SP = 1;
        for (int sp = 2; sp <= 2; sp++) {   // SP=3 在 k55 上比 SP=2 慢 0.8%（L2 占用更大），上限取 2
            long PWs = 16 * ((m4a - 1) / 16) + 80 + 64L * (sp - 1);
            if (PWs < m4a + 64 + 64L * (sp - 1)) PWs = m4a + 64 + 64L * (sp - 1);
            PWs = (PWs + 15) & ~15L;
            const long ring = (KH + 3) * pow2_stride(16L * PWs);
            const int fits_l2 = ring + rbytes <= 400L * 1024;
            const int fits_slice = !slice_ovl || chunks < 1 || (chunks + 4 * (PWs / 16) <= (KH + 3) * chunks);
            if (fits_l2 && fits_slice) SP = sp;
        }
    }
    const long BW = 256L * SP;
    const long NB = (outW + BW - 1) / BW;              // 列块数
    const long G = (outH + 3) / 4;                     // 行组数（每组 4 行输出）
    const long NS = KH + 3;                            // 环形缓冲槽数 = 每组需要的输入行数 = Y 步数
    // 关键（alias 探针）：一条载入流在一行内跨越 4 KB 边界会让整行慢 20–100%。因此 R 的行距与环形缓冲的槽距
    // 都取 2 的幂（≤4 KB 时整除 4 KB），保证 b 流（一行 R）与 a 流（一个槽内的 4 个平面）都不跨页。
    const long RSB = pow2_stride(16L * (KW + 6));       // 打包 kernel 每个 Y 的字节数（≥ 16(KW+6)）
    const long RS = RSB / 4;                           // 每个 Y 的 float 数（含填充）
    // 每平面宽度（元素）：对齐载入读到 16*floor((m4-1)/16)+80（+64(SP-1)）；尾步读到 m4+64
    const long m4 = (KW + 3) / 4, rem = (KW + 3) % 4;
    long PW = 16 * ((m4 - 1) / 16) + 80 + 64L * (SP - 1);
    if (PW < m4 + 64 + 64L * (SP - 1)) PW = m4 + 64 + 64L * (SP - 1);
    PW = (PW + 15) & ~15L;
    const long SB = pow2_stride(16L * PW);             // 槽距（字节，4 个平面 + 填充）
    const long slot_floats = SB / 4;
    const long ring_floats = NS * slot_floats;
    const long ring_stride = (ring_floats + 1023) & ~1023L;    // 线程间 4 KB 对齐
    // 诊断模式：第 1/2 次调用（基准的校验与预热，不计时）开分相计时；第 3 次（计时）只记每线程总时长与主频，汇总延后到进程退出时打印
    const int prof = g_knobs.prof ? g_knobs.prof : (g_diag_on && g_call + 1 <= 2);
    const int pf_in = g_knobs.pf_in;                  // 预取下一行组的原始输入行
    const int pf_out = g_knobs.pf_out;                // 预取本行组的输出行（写）
    const int postart_env = g_knobs.postart;          // >0 覆盖输出预取起始行数（调参用）
    // 按 pass 长度特化：长 pass（KH+3 > 64，即 k81）每 pass 流过 L1 的平面+R 数据远超 L1 容量 →
    // DRAM 预取只进 L2（不挤热线），且 pass 内回写不划算（预取的输出线到回写时已被挤出）；短 pass 反之。
    const int long_pass = (KH + 3) > 64;
    const int store_asm = g_knobs.store_asm >= 0 ? g_knobs.store_asm : !long_pass;   // jc=3/2/1 行回写与 pass 末三行重叠
    int pf_l2 = g_knobs.pf_l2 >= 0 ? g_knobs.pf_l2 : long_pass;                     // DRAM 预取目标层级（BR 时下面改为 L2）
    g_build_uzp = g_knobs.uzp;                        // 平面构建用 ld1w+uzp（1）或 ld4w（0）

    // 边界行（BR）方案：Y 循环少跑 br_pre 个首行、br_post 个尾行，对应的 (输出行, kernel 行) 对由 fmla 扫描完成，
    // 半步（8 条 fmla）插在步之间：稠密时每行 m4 + #A 块组 个半步 = 一半那么多 X' 步；放不完的由 pass 末排空兜底。
    long br_pre = 0, br_post = 0, KPS = 0;
    if (g_knobs.br && KH >= 8 && m4 >= 2) {
        const long cand[3][3] = {{2, 2, 6}, {2, 1, 4}, {1, 1, 2}};   // {首行数, 尾行数, 对数}
        long halves = m4;                                              // 稠密时每行半步数：每块组 1 个 + A 型块组再 1 个
        for (long b = 0; b < m4; b++) if ((b % 16) % 3 == 0) halves++;
        for (int i = 0; i < 3 && !br_pre; i++) {
            const long rows = NS - cand[i][0] - cand[i][1];
            if (rows >= 2 && 2 * cand[i][2] * (KW + 3) <= rows * halves) { br_pre = cand[i][0]; br_post = cand[i][1]; }
        }
        if (br_pre) { KPS = 16; while (KPS < KW + 7) KPS <<= 1; }
    }
    // BR 时 DRAM 预取只进 L2：sweep 的 a 线/平面热线更需要 L1（k39 +0.4%、k55 +1.2%、k41 ±0）
    if (br_pre && g_knobs.pf_l2 < 0) pf_l2 = 1;
    if (br_pre) {
        size_t Kneed = (size_t)KH * KPS;
        if (g_Kpcap < Kneed) { free(g_Kp); g_Kp = alloc_aligned(Kneed * sizeof(float)); g_Kpcap = Kneed; }
        if (!g_Kp) br_pre = br_post = 0;
    }
    // 打包 kernel（含 X' 方向的零填充；行末留有对齐填充，prfm 越界无害）
    size_t Rneed = (size_t)(NS + 1) * RS;
    if (g_Rcap < Rneed) { free(g_R); g_R = alloc_aligned(Rneed * sizeof(float)); g_Rcap = Rneed; if (g_R) memset(g_R, 0, Rneed * sizeof(float)); }
    size_t Pneed = (size_t)ring_stride * nth;
    if (g_Pcap < Pneed) { free(g_P); g_P = alloc_aligned(Pneed * sizeof(float)); g_Pcap = Pneed; }
    {
        size_t stride = ((size_t)2 * NS + 8) & ~(size_t)7;   // 2NS+1 项（pass 末行会预载"下一行"的表项，不使用）
        size_t need = stride * nth + 8;
        if (g_tab_cap < need) { free(g_tab); g_tab = alloc_aligned(need * sizeof(uint64_t)); g_tab_cap = need; }
        g_tab_stride = stride;
    }
    if (!g_R || !g_P || !g_tab) { conv2d_generic(in, H, W, k, KH, KW, out); return; }

    // 每块 tile 数（64 列一个 tile）；按 (outW, BW) 缓存
    static int* TBc = NULL; static long TBc_w = -1, TBc_bw = -1, TBc_sum = 0;
    if (TBc_w != outW || TBc_bw != BW) {
        free(TBc); TBc = malloc(sizeof(int) * NB); TBc_sum = 0;
        for (long b = 0; b < NB; b++) {
            long w = outW - b * BW; if (w > BW) w = BW;
            TBc[b] = (int)((w + 63) / 64);
            TBc_sum += TBc[b];
        }
        TBc_w = outW; TBc_bw = BW;
    }
    int* TB = TBc;
    const long Wtot = G * TBc_sum;

#ifdef CONV_DEBUG_BR
    { static int once = 0; if (!once) { once = 1; br_selftest(); } }
#endif
    // kernel 缓存：与上次调用的 kernel 逐字节相同（且 R/Kp 缓冲未重分配、形状相同）→ 直接复用打包结果；否则主线程现在打包
    static float* kcopy = NULL; static size_t kcopy_n = 0; static long ck_KH = -1, ck_KW = -1, ck_NS = -1, ck_RS = -1, ck_KPS = -1, ck_br = -1;
    static float* ck_R = NULL; static float* ck_Kp = NULL;
    const size_t kn = (size_t)KH * KW;
    int rpacked = (kcopy && kcopy_n == kn && ck_KH == KH && ck_KW == KW && ck_NS == NS && ck_RS == RS && ck_KPS == KPS && ck_br == br_pre &&
                   ck_R == g_R && ck_Kp == g_Kp && memcmp(kcopy, k, kn * sizeof(float)) == 0);
    if (!rpacked) {
        if (kcopy_n < kn) { free(kcopy); kcopy = malloc(kn * sizeof(float)); kcopy_n = kcopy ? kn : 0; }
        if (kcopy) memcpy(kcopy, k, kn * sizeof(float));
        for (long Y = 0; Y < NS; Y++) {
            float* r = g_R + Y * RS;
            for (long Xp = 0; Xp < KW + 6; Xp++) {
                const long x = Xp - 3;
                for (int jc = 0; jc < 4; jc++) { const long y = Y - 3 + jc; r[Xp * 4 + jc] = (y >= 0 && y < KH && x >= 0 && x < KW) ? k[y * KW + x] : 0.0f; }
            }
        }
        if (br_pre) for (long kj = 0; kj < KH; kj++) { float* r = g_Kp + kj * KPS; for (long z = 0; z < KPS; z++) r[z] = (z >= 3 && z < KW + 3) ? k[kj * KW + z - 3] : 0.0f; }
        ck_KH = KH; ck_KW = KW; ck_NS = NS; ck_RS = RS; ck_KPS = KPS; ck_br = br_pre; ck_R = g_R; ck_Kp = g_Kp;
        rpacked = (kcopy != NULL);   // 复制失败则下次仍走并行打包
    }
    double t_pre = (prof || g_diag_on) ? omp_get_wtime() : 0;
    uint64_t c_pre = prof ? cyc() : 0;
    prof_t* prs = prof ? calloc(nth, sizeof(prof_t)) : NULL;
    const uint64_t call_id = ++g_call;

    ctx_t ctx = { in, k, out, H, W, KH, KW, outH, outW, BW, NB, G, NS, RS, m4, rem, PW, slot_floats, ring_stride, Wtot,
                  KPS, br_pre, br_post,
                  SP, prof, pf_in, pf_out, 0, slice_ovl, postart_env, store_asm, pf_l2, rpacked, TB, c_pre, prs, call_id };
    __atomic_store_n(&g_rcount.v, 0, __ATOMIC_RELEASE);
    g_pool_wfe = g_knobs.poolwfe;
#ifdef CONV_ROWPROF
    if (call_id == 2) { size_t n = 1u << 22; g_rowts = malloc(n * sizeof(uint64_t)); g_rowts_cur = g_rowts; g_rowts_end = g_rowts ? g_rowts + n : NULL; }
#endif
    run_parallel(nth, &ctx, g_knobs.pool);
#ifdef CONV_ROWPROF
    if (call_id == 2 && g_rowts) {
        // 按 pass 切分：每 pass = Ymain 个行首戳 + 1 个结束戳（bit63）。统计每个行号的平均时长、pass 末行、pass 间隙
        const double ns = 1e9 / (double)cyc_hz();
        long Ym = -1; double rowsum[128] = {0}; long rowcnt[128] = {0}; double gapsum = 0, passsum = 0; long npass = 0, ngap = 0;
        uint64_t* q = g_rowts; uint64_t prev_end = 0, prev_t1 = 0; double pro = 0, postc = 0, prec = 0; long npro = 0, npostc = 0, nprec = 0;
        const uint64_t TMASK = ~(0xfull << 60);
        while (q < g_rowts_cur) {
            if ((*q >> 60) == 2) {   // 标记 2 → 下一项是首行戳
                uint64_t t2 = *q & TMASK; q++;
                if (q < g_rowts_cur && (*q >> 60) == 0) { pro += (double)(*q - t2); npro++; }
                if (prev_t1) { prec += (double)(t2 - prev_t1); nprec++; }
                continue;
            }
            if ((*q >> 60) == 1) { prev_t1 = *q & TMASK; if (prev_end) { postc += (double)(prev_t1 - prev_end); npostc++; } q++; continue; }
            uint64_t* e = q; while (e < g_rowts_cur && !(*e >> 63)) e++;
            if (e >= g_rowts_cur) break;
            long rows = e - q; if (rows > 0 && rows < 128) {
                if (Ym < 0) Ym = rows;
                if (rows == Ym) {
                    for (long i = 0; i < rows; i++) { uint64_t t1 = (i + 1 < rows) ? q[i + 1] : (*e & TMASK); rowsum[i] += (double)(t1 - q[i]); rowcnt[i]++; }
                    passsum += (double)((*e & TMASK) - q[0]); npass++;
                    if (prev_end) { gapsum += (double)(q[0] - prev_end); ngap++; }
                }
            }
            prev_end = *e & TMASK; q = e + 1;
        }
        if (npass > 0) printf("[rowprof] gap breakdown (ns): post-pass C (extract+store) %.0f | pre-pass C (claim/queue/ZA init) %.0f | asm prologue to row 0 %.0f\n",
                              npostc ? postc / npostc * (1e9 / (double)cyc_hz()) : 0, nprec ? prec / nprec * (1e9 / (double)cyc_hz()) : 0, npro ? pro / npro * (1e9 / (double)cyc_hz()) : 0);
        if (npass > 0) {
            printf("[rowprof] %ldx%ld k%ldx%ld thread0: %ld passes of %ld rows | pass avg %.0f ns | inter-pass gap avg %.0f ns (%.1f%%) | per-row avg ns (cycles@1.55GHz):\n",
                   (long)H, (long)W, (long)KH, (long)KW, npass, Ym, passsum / npass * ns, ngap ? gapsum / ngap * ns : 0, ngap ? 100.0 * (gapsum / ngap) / (passsum / npass) : 0);
            for (long i = 0; i < Ym; i++) printf("%s%ld:%.0f(%.0f)", i ? " " : "  ", i, rowsum[i] / rowcnt[i] * ns, rowsum[i] / rowcnt[i] * ns * 1.55);
            printf("\n");
        }
        free(g_rowts); g_rowts = g_rowts_cur = g_rowts_end = NULL;
    }
#endif
    if (g_diag_on) {
        static int env_done = 0;
        if (!env_done) { env_done = 1; diag_print_env(nth); struct sigaction sa; memset(&sa, 0, sizeof sa); sa.sa_sigaction = diag_sigill; sa.sa_flags = SA_SIGINFO; sigaction(SIGILL, &sa, NULL); sigaction(SIGSEGV, &sa, NULL); sigaction(SIGBUS, &sa, NULL); atexit(diag_atexit); }
        const double tick_ms = 1e3 / (double)cyc_hz();
        double g1n = 1e9, g1x = 0, g1s = 0; uint64_t tn = ~0ull, tx = 0; double ts = 0;
        for (int t = 0; t < nth; t++) { const diag_t* d = &g_diag[t]; double g = d->ghz1; if (g < g1n) g1n = g; if (g > g1x) g1x = g; g1s += g;
                                        uint64_t tt = d->c1 - d->c0; if (tt < tn) tn = tt; if (tt > tx) tx = tt; ts += (double)tt; }
        const diag_sum_t ds = { (unsigned long)call_id, (long)H, (long)W, (long)KH, (long)KW, (omp_get_wtime() - t_pre) * 1e3, (t_pre - t_entry) * 1e3,
                                tn * tick_ms, ts / nth * tick_ms, tx * tick_ms, g1n, g1s / nth, g1x, 0 };
        if (call_id <= 2) {
            if (call_id == 1)
                printf("[conv-diag] params %ldx%ld k%ldx%ld: SP %d NS %ld PW %ld br %ld/%ld long_pass %d pf_l2 %d store_asm %d slice %d pf_in %d pf_out %d items %ld\n",
                       (long)H, (long)W, (long)KH, (long)KW, SP, NS, PW, br_pre, br_post, long_pass, pf_l2, store_asm, slice_ovl, pf_in, pf_out, Wtot);
            printf("[conv-diag] call %lu %ldx%ld k%ldx%ld: region %.3f ms | pre %.3f | thr total min/avg/max %.3f/%.3f/%.3f ms | ghz@end min/avg/max %.3f/%.3f/%.3f\n",
                   ds.call, ds.H, ds.W, ds.KH, ds.KW, ds.region, ds.pre, ds.tn, ds.ta, ds.tx, ds.g1n, ds.g1a, ds.g1x);
        } else if (g_diag_deferred_n < 8) {
            g_diag_deferred[g_diag_deferred_n++] = ds;
            if (getenv("CONV_DIAG_THR")) { for (int t = 0; t < nth; t++) g_diag_thr_ms[t] = (g_diag[t].c1 - g_diag[t].c0) * tick_ms; g_diag_thr_n = nth; }
        }
    }
    if (prof) {
        double ms = 1e3 / (double)cyc_hz();
        prof_t mn = prs[0], mx = prs[0], sum = {0, 0, 0, 0, 0, 0, 0, 0};
        for (int t = 0; t < nth; t++) {
            prof_t* p = &prs[t];
#define ACC(f) do { if (p->f < mn.f) mn.f = p->f; if (p->f > mx.f) mx.f = p->f; sum.f += p->f; } while (0)
            ACC(build); ACC(kern); ACC(store); ACC(total); ACC(enter);
#undef ACC
        }
        if (g_diag_on) {
            printf("[conv-diag] call %lu phases: kern avg/max %.3f/%.3f ms | build avg/max %.3f/%.3f | store avg/max %.3f/%.3f | enter max %.3f | items/thread %.1f\n",
                   (unsigned long)call_id, sum.kern * ms / nth, mx.kern * ms, sum.build * ms / nth, mx.build * ms, sum.store * ms / nth, mx.store * ms, mx.enter * ms,
                   (double)Wtot / nth);
            if (call_id == 2) {
                double g0n = 1e9, g0x = 0, g0s = 0, fn = 1e9, fx = 0, fs = 0, trd = 0, twr = 0, tpf = 0, tnt = 0, gfn = 1e9, gfx = 0, gfs = 0, f2s = 0, f2x = 0;
                for (int t = 0; t < nth; t++) {
                    const diag_t* d = &g_diag[t];
                    g0n = d->ghz0 < g0n ? d->ghz0 : g0n; g0x = d->ghz0 > g0x ? d->ghz0 : g0x; g0s += d->ghz0;
                    fn = d->fmopa_ns < fn ? d->fmopa_ns : fn; fx = d->fmopa_ns > fx ? d->fmopa_ns : fx; fs += d->fmopa_ns;
                    trd = d->t_rd > trd ? d->t_rd : trd; twr = d->t_wr > twr ? d->t_wr : twr; tpf = d->t_pfwr > tpf ? d->t_pfwr : tpf; tnt = d->t_nt > tnt ? d->t_nt : tnt;
                    gfn = d->ghz_fm < gfn ? d->ghz_fm : gfn; gfx = d->ghz_fm > gfx ? d->ghz_fm : gfx; gfs += d->ghz_fm; f2s += d->fmopa_ns2; f2x = d->fmopa_ns2 > f2x ? d->fmopa_ns2 : f2x;
                }
                const double bytes = (double)nth * (double)DIAG_BW_BYTES;
                printf("[conv-diag] probes: ghz@start min/avg/max %.3f/%.3f/%.3f | fmopa ns min/avg/max %.3f/%.3f/%.3f (= %.2f cyc @ avg ghz) | "
                       "bw GB/s read %.1f, st1w %.1f, pstl2keep+st1w %.1f, stnt1w %.1f\n", g0n, g0s / nth, g0x, fn, fs / nth, fx, (fs / nth) * (g0s / nth),
                       trd > 0 ? bytes / trd / 1e9 : 0, twr > 0 ? bytes / twr / 1e9 : 0, tpf > 0 ? bytes / tpf / 1e9 : 0, tnt > 0 ? bytes / tnt / 1e9 : 0);
                printf("[conv-diag] all-core fmopa burst 15 ms: fmopa ns avg/max %.3f/%.3f (= %.2f GHz if 2 cyc) | ghz right after burst min/avg/max %.3f/%.3f/%.3f | "
                       "droop vs start %.1f%%\n", f2s / nth, f2x, 2.0 / (f2s / nth), gfn, gfs / nth, gfx, 100.0 * (1.0 - (gfs / nth) / (g0s / nth)));
                { double hs = 0, qs = 0, gh = 0; int hn = 0, qn2 = 0;
                  for (int t = 0; t < nth; t++) { if (g_diag[t].fm_half > 0) { hs += g_diag[t].fm_half; gh += g_diag[t].ghz_half; hn++; } if (g_diag[t].fm_quarter > 0) { qs += g_diag[t].fm_quarter; qn2++; } }
                  printf("[conv-diag] partial-core bursts: half (%d cores) fmopa ns %.3f (= %.2f GHz) ghz %.3f | quarter (%d cores) fmopa ns %.3f (= %.2f GHz)\n",
                         hn, hn ? hs / hn : 0, hn ? 2.0 / (hs / hn) : 0, hn ? gh / hn : 0, qn2, qn2 ? qs / qn2 : 0, qn2 ? 2.0 / (qs / qn2) : 0); }
            }
            fflush(stdout);
        }
        if (g_knobs.prof && !g_diag_on)
        fprintf(stderr, "[conv prof] SP %d br %ld/%ld | pre %.3f ms | region %.3f ms | go at %.4f..%.4f enter max %.3f | thread total min/avg/max %.3f/%.3f/%.3f | "
                        "build %.3f/%.3f | kern %.3f/%.3f | store %.3f/%.3f (avg/max ms)\n",
                SP, br_pre, br_post,
                (t_pre - t_entry) * 1e3, (omp_get_wtime() - t_pre) * 1e3, (g_prof_c_go - c_pre) * ms, (g_prof_c_go2 - c_pre) * ms, mx.enter * ms, mn.total * ms, sum.total * ms / nth, mx.total * ms,
                sum.build * ms / nth, mx.build * ms, sum.kern * ms / nth, mx.kern * ms, sum.store * ms / nth, mx.store * ms);
        if (prof > 1) {
            for (int t = 0; t < nth; t++)
                fprintf(stderr, "  t%02d cpu%3d enter %.4f total %.3f kern %.3f build %.3f store %.3f items %lu steals %lu\n", t, (int)prs[t].cpu,
                        prs[t].enter * ms, prs[t].total * ms, prs[t].kern * ms, prs[t].build * ms, prs[t].store * ms, (unsigned long)prs[t].items, (unsigned long)prs[t].steals);
        }
        free(prs);
    }
}
#endif // CONV_SME

// ==================== 入口 ====================
void conv2d(const CONVFLOAT* input, CONVINT inputHeight, CONVINT inputWidth,
            const CONVFLOAT* kernel, CONVINT kernelHeight, CONVINT kernelWidth, CONVFLOAT* output)
{
    const long outH = inputHeight - kernelHeight + 1;
    const long outW = inputWidth - kernelWidth + 1;
    if (outH <= 0 || outW <= 0 || kernelHeight <= 0 || kernelWidth <= 0) return;
#ifdef CONV_SME
    if (sme_available()) {
        const double t_in = g_diag_on ? omp_get_wtime() : 0;
        discover_cpus();
        int nth = omp_get_max_threads();
        if (g_ncpu > 0 && nth > g_ncpu) nth = g_ncpu;
        if (nth < 1) nth = 1;
        read_knobs();
        int use_roll = g_knobs.roll > 0 || (g_knobs.roll < 0 && roll_auto(inputHeight, inputWidth, kernelHeight, kernelWidth));
        if (use_roll && roll_shape_ok(inputHeight, inputWidth, kernelHeight, kernelWidth))
            conv2d_roll(input, inputHeight, inputWidth, kernel, kernelHeight, kernelWidth, output, nth);
        else
            conv2d_sme(input, inputHeight, inputWidth, kernel, kernelHeight, kernelWidth, output, nth);
        if (g_diag_on && g_diag_deferred_n > 0) g_diag_deferred[g_diag_deferred_n - 1].total = (omp_get_wtime() - t_in) * 1e3;   // 函数级总时长
        return;
    }
#endif
    conv2d_generic(input, inputHeight, inputWidth, kernel, kernelHeight, kernelWidth, output);
}
