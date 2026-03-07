# HEARTBEAT.md

## Strict output contract (highest priority)
- Healthy: output exactly `HEARTBEAT_OK`
- Unhealthy: output exactly one line `ALERT: <reason>`
- No extra words, no JSON, no markdown, no second line

## Decision scope
- heartbeat 是 main session 的周期性检查，共享上下文
- 可以调用所有工具，包括 sessions_spawn
- 只做：检测 → 推进 → 必要时告警

## 子代理回执检查 (主链路) ⭐⭐⭐⭐⭐

**每次 heartbeat 必须执行**：

```bash
~/.openclaw/workspace/tools/handle-subagent-complete --json
```

**根据返回结果执行**：

| action | 执行 |
|--------|------|
| `spawn_next` | 检查 `spawns` 数组，对每个任务执行 sessions_spawn |
| `notify_user` | 发送 message 给用户 |
| `none` | 继续下一步健康检查 |

**重要**：
- 如果 action != "none"，不输出 HEARTBEAT_OK，直接执行相应操作
- spawn_next 时，需要先激活步骤，再 spawn

## Workflow health checks
重点关注：
- `pending_count`
- `receipt_age_p95`
- `stuck_claimed_count`

## Do not do in heartbeat
- 不启动新项目
- 不进行复杂业务判断
- 不长时间阻塞
- 不在心跳中向用户输出长解释
