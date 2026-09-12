#!/usr/bin/env python3
"""v57 归因诊断变体（结果错误、仅测时序，绝不进产品/提交包）：
逐个跳过 pairf4 事件块 / K4 拷贝 / K4 事件 / K9 拷贝 / K9 事件，量化各段在真实内核中的时间占比。"""
from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
src = (root / 'conv2d.c').read_text()
out = root / 'build' / 'v57'
out.mkdir(parents=True, exist_ok=True)


def gen(name, repls):
    s = src
    for old, new, cnt in repls:
        n = s.count(old)
        assert n == cnt, f'{name}: anchor {old[:60]!r} found {n} times, expected {cnt}'
        s = s.replace(old, new)
    (out / f'{name}.c').write_text(s)
    print(name, 'ok')


# 基线 = 原样拷贝（同一目录内编译，排除路径差异）
gen('base', [])

# pairf4：SEL_OUT 后直接跳过事件块（该锚串在 pairf4 中唯一：其后紧跟 4 链窗口注释）
gen('pf4_noev', [(
    'SEL_OUT\n        // 事件：cA ∈ [CF0-3, CF0] → 4 条 fmla 链',
    'SEL_OUT\n        "b 5f\\n\\t"\n        // 事件：cA ∈ [CF0-3, CF0] → 4 条 fmla 链',
    1)])

# K4：跳过事件（k4 的事件判定锚串）
gen('k4_noev', [(
    'WRAP_B(x2) SEL_OUT\n        "cmp x27, x24\\n\\t" "b.hs 4f\\n\\t"\n        "lsl w12, w27, #2\\n\\t"',
    'WRAP_B(x2) SEL_OUT\n        "b 4f\\n\\t"\n        "cmp x27, x24\\n\\t" "b.hs 4f\\n\\t"\n        "lsl w12, w27, #2\\n\\t"',
    1)])

# K4：跳过行内拷贝（穿插 + 尾拷都空转；序言整行拷贝保留）
gen('k4_nocopy', [(
    'A.ovn = A.it - 1 < A.ncp_full ? A.it - 1 : A.ncp_full;         // 穿插的整块数 ≤ 外步数-1（纯步循环 ≥ 1）\n    if (A.ovn < 0) A.ovn = 0;\n    A.ovr = A.ncp_full - A.ovn;',
    'A.ovn = 0; A.ovr = 0; A.ncp_tail = 0;   // 诊断：不拷行（结果错误，仅测时序）',
    1)])

# K9：跳过事件（k8f 的事件头）
gen('k9_noev', [(
    'WRAP_B(x2) SEL_OUT\n        "ldr x12, [%[A], #216]\\n\\t"\n        "cmp x27, x12\\n\\t"\n        "b.eq 80f\\n\\t"',
    'WRAP_B(x2) SEL_OUT\n        "b 4f\\n\\t"\n        "ldr x12, [%[A], #216]\\n\\t"\n        "cmp x27, x12\\n\\t"\n        "b.eq 80f\\n\\t"',
    1)])

# K9：跳过行内平面拷贝（保留序言那次；行内 K9_CP 替换为空）
gen('k9_nocopy', [(
    '"csel x22, x0, x22, eq\\n\\t"\n        "add x21, x0, x26\\n\\t"\n        K9_CP(x17)\n        "ldr x25, [%[A], #256]\\n\\t"',
    '"csel x22, x0, x22, eq\\n\\t"\n        "add x21, x0, x26\\n\\t"\n        "ldr x25, [%[A], #256]\\n\\t"',
    1)])

# ---- 拷贝成分分解（结果仍位精确！只去预取/换指令，值不变）----
# K4：穿插拷贝去掉 4 条 prfm（量 prfm 槽位占比；位精确）
gen('k4_noprf', [(
    '"prfm pldl2keep, [x21]\\n\\t" "prfm pldl2keep, [x21, #64]\\n\\t" "prfm pldl2keep, [x21, #128]\\n\\t" "prfm pldl2keep, [x21, #192]\\n\\t"\n        "ld4w {z25.s, z26.s, z27.s, z28.s}, p0/z, [x13]\\n\\t"',
    '"ld4w {z25.s, z26.s, z27.s, z28.s}, p0/z, [x13]\\n\\t"',
    1)])
# K9：K9_CP 去掉每块 2 条 prfm（位精确）
gen('k9_noprf', [(
    '"90:\\n\\t" \\\n        "prfm pldl2keep, [x21]\\n\\t" "prfm pldl2keep, [x21, #64]\\n\\t" \\\n        "ld2w {z0.s, z1.s}, p0/z, [x12]\\n\\t"',
    '"90:\\n\\t" \\\n        "ld2w {z0.s, z1.s}, p0/z, [x12]\\n\\t"',
    1)])

# ---- 第三轮：补齐 pair 族拷贝与 k41/k55 事件归因（均为诊断，仅时序）----
# pairf4：行首整块拷贝跳过（ROW_HEAD_COPY4 仅 pairf4 使用；尾拷保留）
gen('pf4_nocopy', [(
    '"add x22, x0, x1\\n\\t" "cmp x8, #1\\n\\t" "csel x22, x0, x22, eq\\n\\t" "mov x23, x17\\n\\t" \\\n        "ldr x12, [%[A], #168]\\n\\t" \\\n        "cbz x12, 7f\\n\\t" \\\n        "cmp x12, #4\\n\\t"',
    '"add x22, x0, x1\\n\\t" "cmp x8, #1\\n\\t" "csel x22, x0, x22, eq\\n\\t" "mov x23, x17\\n\\t" \\\n        "mov x12, #0\\n\\t" \\\n        "cbz x12, 7f\\n\\t" \\\n        "cmp x12, #4\\n\\t"',
    1)])

# pairf（k41 主力）：事件跳过
gen('pf1_noev', [(
    'SEL_OUT\n        // 事件：cA==CF0 → fmla 残差（z10/z11 存出清零）；cA<16 → A；16≤cA<32 → B；其余无',
    'SEL_OUT\n        "b 5f\\n\\t"\n        // 事件：cA==CF0 → fmla 残差（z10/z11 存出清零）；cA<16 → A；16≤cA<32 → B；其余无',
    1)])

# pairf3（k55 主力）：事件跳过
gen('pf3_noev', [(
    'SEL_OUT\n        // 事件：cA ∈ [CF0-2, CF0] → fmla 链（w24 = 0:KH-3 / 1:KH-2 / 2:KH-1）；cA<16 → A；16≤cA<32 → B',
    'SEL_OUT\n        "b 5f\\n\\t"\n        // 事件：cA ∈ [CF0-2, CF0] → fmla 链（w24 = 0:KH-3 / 1:KH-2 / 2:KH-1）；cA<16 → A；16≤cA<32 → B',
    1)])

# singlef2（k55 次主力）：事件跳过
gen('sf2_noev', [(
    'SEL_OUT\n        // 事件：cA==CF1 → fmla1；cA==CF2 → fmla2；cA<nvA → ZA（三者互斥：CF=20/21 ≥ nvA=16）',
    'SEL_OUT\n        "b 5f\\n\\t"\n        // 事件：cA==CF1 → fmla1；cA==CF2 → fmla2；cA<nvA → ZA（三者互斥：CF=20/21 ≥ nvA=16）',
    1)])

# k8（k41 次主力）：行拷贝跳过（穿插+尾拷空转）
gen('k8_nocopy', [(
    'ka_t A; fill_args(&A, P, 2, 896, 126 + P->steps);\n    asm volatile(\n        LOAD_ARGS\n        "ldr x7, [%[A], #136]\\n\\t"      // it = steps/2',
    'ka_t A; fill_args(&A, P, 2, 896, 126 + P->steps);\n    A.ovn = 0; A.ovr = 0; A.ncp_tail = 0;   // 诊断：不拷行（结果错误，仅测时序）\n    asm volatile(\n        LOAD_ARGS\n        "ldr x7, [%[A], #136]\\n\\t"      // it = steps/2',
    1)])

print('all variants generated to', out)
