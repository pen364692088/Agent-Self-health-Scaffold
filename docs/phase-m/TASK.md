# Phase M: selected manual_enable_only Agents 受控 pilot

## 目标
从 6 个 manual_enable_only agents 中，分批选择对象进入受控 pilot，验证从"最小接入"到"真实试运行"的闭环。

## 当前正式基线
- **continue_default_enabled**: main, audit, coder
- **manual_enable_only**: default, healthcheck, acp-codex, codex, mvp7-coder, cc-godmode

## 强制约束
1. 不修改 3 个 continue_default_enabled 的正式状态
2. 不新增正式状态词典
3. 不要求补齐 Telegram token
4. 不把"可调用"表述为"已稳定"
5. Batch M1: default + healthcheck (低风险)
6. Batch M2: acp-codex, codex, mvp7-coder (中风险)
7. Batch M3: cc-godmode (高风险，单独治理)

## 执行分期
- M0 范围冻结
- M1 pilot 候选确认
- M2 pilot 启用与接入锁定
- M3 单 Agent 运行观察
- M4 治理演练
- M5 晋级决策

## 完成标准
每个进入 pilot 的 agent 都必须有独立观察证据、独立治理演练、独立决策。
