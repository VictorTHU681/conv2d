# 同字节对照与共享程序 PMU 诊断

基线为已验收的 K5 标量展开 `ce57939 / 0136da05`。以下仅解释诊断设计与观测，
没有新增生产内核优化；工具、作业与日志随 v64 汇总。

## 同字节程序对照

作业 **1590409**，cn20490，2026-09-13 15:14:26–15:15:31。
三个程序使用已验证的同一份二进制：control0/1 是同 inode 的硬链接，control2 是独立副本。
日志验证哈希、大小与 inode 关系；路径等长，六种完整排列、四形状、DDR/HBM，共 720 次
计时哈希通过。下载后的三个二进制哈希也与运行前一致。

六轮进程平均 GFLOPS 的中位数比例，观察到共享 inode 对照从 -0.36% 到 +0.04%，
独立副本从 -0.28% 到 +0.28%。所有离群值保留，包括共享 inode 对照 DDR41 -4.88%、
HBM39 -2.38%、HBM41 -6.37%。不能把这些范围当作通用噪声界限，也不能从中确定
先前偏移的唯一原因，或将比例从其他作业结果中扣除。

[完整结果](../results/post63/identical-binary/summary.md)、
[运行后二进制审计](../results/post63/identical-binary/binary_audit.txt)。

## 共享程序 PMU 诊断

作业 **1590635**，cn20490，2026-09-13 15:34:32–15:37:32。
同一程序包含 baseline/early/spread 三种 K5，通过相同间接调用位置分派；服务器 nm
确认三个入口均 128 字节对齐。只在独立诊断中读取 CONV_K5_ORDER、CONV_K5_PMU。
每个工作线程独立计数用户态 CPU 周期和指令数；计数范围为整个 SME worker 循环，
包括领取任务、等待、续算状态、pair 与 K5，不是单独 K5 的计数。

所有 perf_event_open、ioctl、read 均在 sme_start 之前或 sme_stop 之后执行。
Linux 系统调用会清除 PSTATE.SM，因此计数系统调用不能插入被测流式计算段。
[Linux SME ABI](https://www.kernel.org/doc/html/v6.16/arch/arm64/sme.html)。
计数使用 GROUP、ID、TIME_ENABLED、TIME_RUNNING；IOC_RESET 不重置时间字段，
所以逐次记录前后时间差，并核对事件 ID 与运行比例。
[perf_event_open 文档](https://man7.org/linux/man-pages/man2/perf_event_open.2.html)。

三个设置共 1,455 项状态/保护页检查通过。六排列比较及六轮开关对照共 60 个进程，
15,960 条线程记录、300 次计时哈希通过，工作量与表大小一致。所有运行/启用时间比率
为 1.000000000，报告未缩放的原始计数；三个下载的二进制与运行前哈希一致。

K5 区域均时（µs/线程）：DDR baseline 943.756、early 948.163、spread 963.995；
HBM 920.467、927.410、933.570。整个 worker 的指令数约 2,318.7 万/线程，
各模式接近；区域时间与 CPI 无法确定物理执行端口。两个候选仍不采用。

计数开关对照的整体 GFLOPS 为 DDR -1.02%、HBM +0.11%，配对范围分别
-3.76%..+1.64%、-2.23%..+1.49%。开销包含计数设置、系统调用、读取及调度扰动，
不能用 HBM 的正中位数宣称插桩无成本。所有插桩结果仅供诊断，不替代原始基准验收。

[完整结果](../results/post63/k5-pmu/summary.md)、
[二进制审计](../results/post63/k5-pmu/binary_audit.txt)、
[入口对齐审计](../results/post63/k5-pmu/symbol_audit.txt)、
[生成器](../tools/gen_post63_k5_pmu.py)、[计数实现](../tools/post63_pmu_scope.inc)。
