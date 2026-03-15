# v3/Memory Kernel 任务分解

## 当前状态
- v3-A: ✅ 完成 (调度与占用控制)
- v3-B: ✅ 完成 (父子任务编排)
- v3-C: ✅ 完成 (Failure Policy Engine)
- v3-D: ⏳ 待实现 (Autonomous Runner)
- v3-E: ⏳ 待实现 (Autonomy Policy Layer)
- Memory Kernel: ⏳ 待实现 (M0-M9)

## 子任务分解

### 子任务 1: v3-D Autonomous Runner
目标: 让系统从"需要人手动触发继续"变成"默认自动启用、自动持续推进"

必须实现:
- service startup loop
- pending task scanner
- scheduler loop
- retry loop
- stuck task detector
- restart recovery loop
- heartbeat / health monitor

### 子任务 2: v3-E Autonomy Policy Layer
目标: 让系统拥有"默认自动推进"的能力，同时明确什么不能自动做

必须实现:
- allowed actions
- forbidden actions
- approval-required actions
- risk levels
- safe-stop conditions
- policy evidence log

### 子任务 3: Memory Kernel M0-M3
目标: 现有记忆能力统一整合

必须实现:
- M0: 全量盘点 (MEMORY_CAPABILITY_AUDIT.md)
- M1: Memory Contract (types.py, policies.py)
- M2: 现有资产统一映射
- M3: 统一查询服务

## 执行策略
按顺序执行，每个子任务完成后验证 Gate
