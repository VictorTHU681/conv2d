// SME2 探针：流式模式下多向量载入 / pn 谓词计数器 / ZT0 是否可用。
// 每项单独 fork 子进程执行，SIGILL 视为不支持。
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/auxv.h>

static int try_run(void (*fn)(void))
{
    pid_t p = fork();
    if (p == 0) { fn(); _exit(0); }
    int st = 0; waitpid(p, &st, 0);
    return WIFEXITED(st) && WEXITSTATUS(st) == 0;
}

static float buf[64] __attribute__((aligned(256)));

__attribute__((noinline)) static void probe_ld1w_x2(void)
{
    asm volatile(
        "smstart\n\t"
        "ptrue pn8.s\n\t"                                  // SME2: 谓词计数器
        "ld1w {z0.s, z1.s}, pn8/z, [%0]\n\t"               // SME2: 多向量连续载入（consecutive）
        "st1w {z0.s, z1.s}, pn8, [%0]\n\t"
        "smstop\n\t" : : "r"(buf) : "z0", "z1", "memory");
}

__attribute__((noinline)) static void probe_ld1w_x4(void)
{
    asm volatile(
        "smstart\n\t"
        "ptrue pn8.s\n\t"
        "ld1w {z0.s-z3.s}, pn8/z, [%0]\n\t"
        "smstop\n\t" : : "r"(buf) : "z0", "z1", "z2", "z3", "memory");
}

__attribute__((noinline)) static void probe_fmla_vg2(void)
{
    asm volatile(
        "smstart\n\t"
        "zero {za}\n\t"
        "mov w8, #0\n\t"
        "fmla za.s[w8, 0, vgx2], {z0.s-z1.s}, z4.s\n\t"    // SME2: ZA 向量组 FMLA
        "smstop\n\t" : : : "z0", "z1", "z4", "memory");
}

__attribute__((noinline)) static void probe_zt0(void)
{
    asm volatile(
        "smstart\n\t"
        "zero {zt0}\n\t"                                    // SME2: ZT0 表
        "smstop\n\t" : : : "memory");
}

int main(void)
{
    unsigned long hw2 = getauxval(AT_HWCAP2);
    printf("HWCAP2=0x%lx SME=%d SME2(bit37?)=%lu\n", hw2, !!(hw2 & (1UL << 23)), (hw2 >> 37) & 1);
    printf("ld1w_x2(consecutive): %s\n", try_run(probe_ld1w_x2) ? "OK" : "SIGILL/不支持");
    printf("ld1w_x4:              %s\n", try_run(probe_ld1w_x4) ? "OK" : "SIGILL/不支持");
    printf("fmla_vgx2:            %s\n", try_run(probe_fmla_vg2) ? "OK" : "SIGILL/不支持");
    printf("zero_zt0:             %s\n", try_run(probe_zt0) ? "OK" : "SIGILL/不支持");
    return 0;
}
