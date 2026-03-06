# HEARTBEAT.md

## Strict output contract (highest priority)
- Healthy: output exactly `HEARTBEAT_OK`
- Unhealthy: output exactly one line `ALERT: <reason>`
- No extra words, no JSON, no markdown, no second line

## Decision scope
- 把 `Cron: HEARTBEAT_OK`、heartbeat poll、monitoring probe 视为纯健康检查，不当作普通聊天。
- 心跳中不做复杂推理、不做大任务、不启动新项目。
- 只做：检测 → 简单恢复 → 必要时告警。

## Workflow health checks
重点关注：
- `pending_count`
- `receipt_age_p95`
- `stuck_claimed_count`

## Recovery rules

### 邮箱异常
- `pending_count > 10` → 优先处理 inbox
- `receipt_age_p95 > 60s` → 检查 worker
- `stuck_claimed_count > 0` → 回收 claimed

### 推荐恢复命令
```bash
subtask-orchestrate status
subagent-inbox recover-claimed
systemctl --user restart subagent-inbox-worker
```

## Do not do in heartbeat
- 不启动新子任务
- 不进行复杂业务判断
- 不长时间阻塞
- 不在心跳中向用户输出长解释
