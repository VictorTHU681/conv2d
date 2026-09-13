// 读 ID_AA64SMFR0_EL1 / ID_AA64PFR1_EL1，解码 SME 版本（Linux EL0 MRS 仿真）。
#include <stdio.h>
#include <sys/auxv.h>

int main(void)
{
    unsigned long smfr0 = 0, pfr1 = 0, zfr0 = 0;
    asm volatile("mrs %0, S3_0_C0_C4_5" : "=r"(smfr0));   // ID_AA64SMFR0_EL1
    asm volatile("mrs %0, S3_0_C0_C4_1" : "=r"(pfr1));    // ID_AA64PFR1_EL1
    asm volatile("mrs %0, S3_0_C0_C4_4" : "=r"(zfr0));    // ID_AA64ZFR0_EL1
    unsigned smever = (smfr0 >> 56) & 0xF;                 // 0=SME1, 1=SME2, 2=SME2p1
    printf("ID_AA64SMFR0_EL1 = 0x%016lx\n", smfr0);
    printf("ID_AA64PFR1_EL1  = 0x%016lx (SME field bits27:24 = %lu)\n", pfr1, (pfr1 >> 24) & 0xF);
    printf("ID_AA64ZFR0_EL1  = 0x%016lx\n", zfr0);
    printf("SMEver(bits59:56) = %u  => %s\n", smever,
           smever == 0 ? "SME (无 SME2)" : smever == 1 ? "SME2" : smever >= 2 ? "SME2p1+" : "?");
    printf("F64F64=%lu I16I64=%lu F32F32(FA64相关)=%lu B16F32=%lu BI32I32=%lu\n",
           (smfr0 >> 48) & 0xF ? 1UL : 0UL, (smfr0 >> 52) & 0xF ? 1UL : 0UL,
           (smfr0 >> 32) & 1, (smfr0 >> 34) & 1, (smfr0 >> 33) & 1);
    unsigned long hw2 = getauxval(AT_HWCAP2);
    printf("HWCAP2 = 0x%lx\n", hw2);
    return 0;
}
