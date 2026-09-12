# conv2d on Kunpeng SME — 鲲鹏 HPC 挑战赛 S2 CONV 赛题

FP32 二维 valid 卷积 `conv2d(in, H, W, k, KH, KW, out)` 的 SME（FMOPA）实现。结果与参考实现逐位一致
（校验 1e-5 绝对误差，低于输出量级的 1 ulp，因此必须保持与参考实现完全相同的 fma 累加链），按 GFLOPS 计分。

## 运行

```bash
bash run.sh    # 编译 + 四个用例（题面判题口径：OMP_NUM_THREADS=38 numactl -N 1）
```

或手动：

```bash
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o conv2d_test -lm   # 或题面的 gcc -O3 ...（文件内 pragma 打开 SME）
OMP_NUM_THREADS=38 numactl -N 1 ./conv2d_test 4096 6144 39 39 1
```

运行期用 HWCAP2 检测 SME；硬件或编译器不支持时自动回退 SVE/标量通用实现（任意合法尺寸均正确）。

## 核心思路

- FMOPA 外积对每个 ZA 元素恰是一次 fma。把卷积映射成外积序列，并保证每个输出元素的累加顺序与参考实现
  （kernel 行主序）完全一致 → 逐位精确。所有实现分支（滚动 / 经典 / SVE / 标量）都满足该性质。
- **滚动形态**（KH ≥ 16 且条带可行时启用，结构性条件，与具体用例尺寸无关）：tile 列 ↔ 输出行残差
  (s+c) mod KH，每列一条独立 fma 链，链满（KH 步）时 mova 切片直接落出连续输出，步数 = KW（X 方向零浪费）。
  残差按 KH 二进制分解成 16×1 对 / 单 16 / 8×2 / 4×4 组；余数残差折进 fmopa 旁并发的索引 fmla 链
  （每步 1 条 ld1rqw + 若干 fmla，链数按分解结构自动选 1/3/4），消掉低利用率的余数组。
- **经典形态**（其余形状）：tile 行 ↔ 输出列（stride 4），tile 列 ↔ 4×4 kernel 偏移，步数 (KH+3)(KW+3)；
  输入行去交织成 4 个平面驻留 L2 环形缓冲，a 向量用对齐载入 + `ext` 生成；整个 pass 的 Y 循环在一段汇编里，
  DRAM 预取、下一组的 ld4w 切片构建、已完成输出行的回写作为块组末尾的附加工作与 fmopa 交错。
  边界行（Y=0/1/KH+1/KH+2 只有少数列在干活）从 fmopa 循环移出，由并发的索引 fmla 半步完成。
- 每次调用都完整执行 kernel 打包（R/kf 查找表由主线程重建，不缓存内容）；线程绑核取自继承的亲和掩码
  （兼容 numactl/taskset），自有线程池调用间自旋（等价 OMP_WAIT_POLICY=ACTIVE），按代价模型静态划分 +
  CAS 工作窃取兜底；按 pass 长度自适应选择预取层级与回写方式（长/短 pass 两套策略）。

## 文件

- `conv2d.c` 实现（单文件，含 SME/SVE/标量三级回退）；`bench_conv.c` 官方基准（未修改）；`run.sh` 编译 + 四例。
- 开发库另有 `tools/test_conv.c`（与参考四重循环逐位比较的泛化测试，固定边界用例 + 随机尺寸）、
  `tools/fbench.c`（快速判题口径 bench）、`tools/drv.c`（分相计时驱动）。

## 环境变量（默认即最优，仅用于实验/回退）

`CONV_ROLL=0` 强制经典形态；`CONV_POOL=0` 回退 OpenMP 并行区；`CONV_BR=0` 关边界行方案；
`CONV_SP`/`CONV_STORE`/`CONV_PFL2` 等微调项见 `conv2d.c` 的 `read_knobs()`；`CONV_NO_SME=1` 强制通用实现。
`CONV_PROFILE=1` 输出分相计时（stderr）。
