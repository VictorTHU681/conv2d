// SME2p1 MOVAZ 硬件支持探测：streaming 模式下执行一条 movaz（ZA 竖切片读取并清零）。
// 支持 → 打印 MOVAZ_OK 与位校验结果；不支持 → SIGILL（作业里捕获退出码）。
// 编译（服务器 clang-18）：clang-18 --target=aarch64-linux-gnu -march=armv9-a+sme2p1 -O2 v57_movaz.c -o v57_movaz
#include <stdio.h>
#include <string.h>

static float src[16] __attribute__((aligned(64)));
static float out1[16] __attribute__((aligned(64)));
static float out2[16] __attribute__((aligned(64)));

int main(void)
{
    for (int i = 0; i < 16; i++) src[i] = (float)(i + 1);
    asm volatile(
        "smstart\n\t"
        "ptrue p0.s\n\t"
        "mov w12, #0\n\t"
        "ld1w {z1.s}, p0/z, [%[s]]\n\t"
        "mova za0v.s[w12, 0], p0/m, z1.s\n\t"      // 写入切片
        "movaz z2.s, za0v.s[w12, 0]\n\t"           // 读取并清零（SME2p1）
        "st1w {z2.s}, p0, [%[o1]]\n\t"
        "mova z3.s, p0/m, za0v.s[w12, 0]\n\t"      // 再读：应为全零
        "st1w {z3.s}, p0, [%[o2]]\n\t"
        "smstop\n\t"
        : : [s]"r"(src), [o1]"r"(out1), [o2]"r"(out2)
        : "p0", "z1", "z2", "z3", "x12", "memory", "cc");
    int ok1 = !memcmp(out1, src, sizeof src);
    int zero = 1;
    for (int i = 0; i < 16; i++) zero &= out2[i] == 0.f;
    printf("MOVAZ_OK read=%s clear=%s\n", ok1 ? "PASS" : "FAIL", zero ? "PASS" : "FAIL");
    return ok1 && zero ? 0 : 1;
}
