# OPENCLAW_ALWAYS_ON_POLICY

## Purpose
将已证明可用的 self-health scaffold 接入 OpenClaw 主系统默认运行链路，使其成为默认常驻、可观测、可审计、可回退的保护层。

## Current State Machine
- `MAIN_SYSTEM_ALWAYS_ON_PENDING`
- `WIRING_ACTIVE_BUT_SOAK_PENDING`
- `MAIN_SYSTEM_ALWAYS_ON_ACTIVE`
- `ROLLBACK_TO_MANUAL_MODE`

## Default Integration Points
以下接入点才算默认链路，不接受独立后台脚本替代：
1. heartbeat hook
2. periodic scheduler / cron / timer
3. preflight
4. doctor
5. execution guard

## Runtime Modes
### quick
- 低成本检查
- 目标接入点：heartbeat hook
- 默认 cooldown：300s
- 预算：单次 < 15s
- 输出：heartbeat telemetry、quick run history、基础 health state

### full
- 深度检查与 summary 刷新
- 目标接入点：periodic scheduler / timer
- 默认 cooldown：3600s
- 预算：单次 < 120s
- 输出：full run history、runtime telemetry、summary status

### gate
- 常驻治理检查
- 目标接入点：preflight / doctor / execution guard
- 默认 cooldown：300s
- 预算：单次 < 30s
- 输出：Gate A/B/C status、解释、history

## Hard Boundaries
- Level A 仅限白名单有限自愈
- Level B proposal-only
- Level C proposal-only
- 不绕过 Gate
- 不破坏 `INSTANCE_1_PROVEN`
- 不把 manual run 冒充 always-on

## Required Safety Controls
- single-run lock
- cooldown window
- dedup window
- execution budget
- soft failure fallback
- 明确 rollback 条件与步骤

## Rollback Conditions
满足任一条件即允许触发回退：
- quick/full/gate 触发风暴
- heartbeat 主循环延迟明显升高
- Gate 输出长期失真或无法解释
- runtime telemetry 持续不刷新
- summary/proposal/incident 异常膨胀

## Rollback Steps
1. 停止 full timer
2. 暂停 quick mode 触发
3. gate 改为只读保守模式
4. 保留 runtime telemetry 文件供审计
5. 状态回退为 `MANUAL_RUN_PROVEN_BUT_ALWAYS_ON_NOT_READY`

## Minimum Safe Mode After Rollback
- 手动运行 `tools/agent-health-check --deep --json`
- 手动运行 `tools/gate-self-health-check --json`
- 保留 proposal-only 边界
- 保留 artifacts 审计痕迹
