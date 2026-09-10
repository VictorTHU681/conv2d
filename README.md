# conv2d on Kunpeng SME — 鲲鹏 HPC 挑战赛 S2 CONV 赛题

FP32 二维 valid 卷积 `conv2d(in, H, W, k, KH, KW, out)` 的 SME（FMOPA）实现，要求与参考实现逐位一致
（校验 1e-5 绝对误差，低于输出量级的 1 ulp），按 GFLOPS 计分；四个用例见 `docs/problem.md`。

## 成绩（本机 38 核 1.55 GHz 判题口径，`OMP_NUM_THREADS=38 numactl -N 1`）

| 用例 | 4096×6144 k39 | 6144×4096 k41 | 4256×6390 k55 | 6390×4256 k81 |
|---|---|---|---|---|
| GFLOPS | 12631 | 12664 | 13805 | 14028 |
| 纯 fmopa 形态下限 | 13000 | 13090 | 13560 | 14020 |

评测机主频 2.0 GHz，成绩约为本机 × 1.27。方法与全部实测记录见 `NOTES.md`。

## 核心思路

- FMOPA 外积对每个 ZA 元素恰是一次 fma，把卷积映射成外积序列并保持 (jk, ik) 行主序 → 逐位精确。
  tile 行 ↔ 输出列（stride 4），tile 列 ↔ 4×4 kernel 偏移（16 列 tile 的 Minkowski 下界），步数 (KH+3)(KW+3)。
- 输入行去交织成 4 个平面驻留 L2 环形缓冲；a 向量用对齐载入 + `ext` 生成；整个 pass 的 Y 循环在一段汇编里，
  DRAM 预取、下一组的 ld4w 切片构建、已完成输出行的回写都作为块组末尾的附加工作与 fmopa 交错。
- **边界行方案**：Y=0/1/KH+1/KH+2 只有少数列在干活，把它们从 fmopa 循环移出，对应的 (输出行, kernel 行) 对由与
  fmopa 并发的索引 `fmla`（每 8 步 ≤ 3 个 8 条的半步）完成：前半算成 ZA 初值，后半在 pass 后续完。
- 自有线程池（调用间自旋）、按 (列块, 4 行组) 静态划分 + relaxed CAS 窃取、按 pass 长度的按用例特化（预取层级、回写方式）。

## 目录

- `conv2d.c` 实现；`bench_conv.c` 官方基准；`run.sh` 判题脚本（编译 + 四例）。
- `tools/test_conv.c` 泛化位精确测试；`tools/fbench.c` 快速判题口径 bench（参考哈希缓存）；`tools/drv.c` 分相计时。
- `probe/` 微架构探针；`jobs/` Donau 作业脚本（`validate_job.sh` 完整验证、`fbench_job.sh`、`accept_zip_job.sh`、探针）。
- `submissions/conv.zip` 提交包（`bash run.sh` 即可）；`NOTES.md` 完整笔记。

## 编译运行

```bash
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp bench_conv.c conv2d.c -o conv2d_test -lm   # 或题面的 gcc -O3 ...（文件内 pragma 打开 SME）
OMP_NUM_THREADS=38 numactl -N 1 ./conv2d_test 4096 6144 39 39 1
gcc -O3 -march=armv9-a+sme+sve2 -fopenmp tools/fbench.c conv2d.c -o fbench -lm && OMP_NUM_THREADS=38 numactl -N 1 ./fbench 4096 6144 39 39 3
```
运行期检测 SME（HWCAP2），没有 SME 或编译器不支持时自动退到 SVE/标量通用实现。
