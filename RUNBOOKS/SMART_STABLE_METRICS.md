# Smart+Stable Metrics Runbook

## 目的
用可量化指标评估「更聪明 + 更稳定」优化是否有效。

## 指标定义
- **first_pass_success_rate**: 工具调用首轮成功率（越高越好）
- **retry_recovery_rate**: 失败后在短窗口内恢复成功率（越高越好）
- **avg_turn_latency_ms**: 工具回合平均耗时（越低越好）
- **avoidable_failure_count**: 可避免错误计数（ENOENT / command not found / unknown session / timeout）
- **tool_error_rate**: 工具结果错误率（越低越好）

## 命令
```bash
# 1) 设 baseline（默认过去24小时）
~/.openclaw/workspace/tools/smart-stable-metrics baseline --hours 24

# 2) 随时比较当前与 baseline
~/.openclaw/workspace/tools/smart-stable-metrics compare --hours 24

# 3) 仅做快照
~/.openclaw/workspace/tools/smart-stable-metrics snapshot --hours 24
```

## 输出位置
- Baseline: `reports/smart_stable/baseline.json`
- Compare: `reports/smart_stable/compare-*.json`
- Snapshot: `reports/smart_stable/snapshot-*.json`

## 解释建议
- first_pass_success_rate ↑ 且 tool_error_rate ↓：质量提升
- retry_recovery_rate 高但首轮成功率低：说明恢复不错，但前置决策仍可优化
- avg_turn_latency 上升明显：检查是否过度使用高思考/重工具路径

## 注意
- 默认排除 cron/heartbeat 会话，避免噪声
- 若需要全量（含 cron），加 `--include-cron`
