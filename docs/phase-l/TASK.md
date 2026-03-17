# Phase L: manual_enable_only Agents 补全与最小接入

## 目标
将 6 个 manual_enable_only agents 补到"最小可接入闭环"，而不是直接晋级 default。

## 强制约束
1. 不新增正式状态词典
2. 不修改 continue_default_enabled 的 3 个 agent
3. 不要求 Telegram token 补齐
4. 允许 runtime-only，但必须有明确调用路径与最小调用验证
5. 不得把"可调用"表述为"已稳定"
6. cc-godmode 单独处理，不与其他 agent 混批

## 对象
- default
- healthcheck
- acp-codex
- codex
- mvp7-coder
- cc-godmode (单独处理)

## 执行分期
- L0 基线冻结与对象确认
- L1 配置补全盘点
- L2 最小接入补全
- L3 最小可调用验证
- L4 治理与边界补全
- L5 最终分流决策

## 完成标准
6 个 agent 都有明确、可执行、可追溯的最小接入结论。
