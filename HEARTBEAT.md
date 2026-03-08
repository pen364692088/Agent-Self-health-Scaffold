# HEARTBEAT.md

## Strict output contract (highest priority)
- Healthy: output exactly `HEARTBEAT_OK`
- Unhealthy: output exactly one line `ALERT: <reason>`
- No extra words, no JSON, no markdown, no second line

## Decision scope
- heartbeat 是 main session 的周期性检查，共享上下文
- 可以调用所有工具，包括 sessions_spawn
- 只做：检测 → 推进 → 必要时告警

---

## Session Recovery Check (每次 heartbeat) ⭐⭐⭐⭐⭐

### 检查步骤

1. **执行恢复检查**
   ```bash
   # 调用恢复工具（静默模式）
   RECOVERY_RESULT=$(session-start-recovery --recover --json 2>/dev/null)
   RECOVERY_EXIT=$?
   
   if [ $RECOVERY_EXIT -ne 0 ]; then
       echo "ALERT: RECOVERY_FAILED"
       exit 0
   fi
   
   # 解析结果
   RECOVERED=$(echo "$RECOVERY_RESULT" | jq -r '.recovered // false')
   IS_NEW_SESSION=$(echo "$RECOVERY_RESULT" | jq -r '.is_new_session // false')
   UNCERTAINTY=$(echo "$RECOVERY_RESULT" | jq -r '.uncertainty_flag // false')
   ```

2. **处理恢复结果**
   
   | 场景 | 动作 |
   |------|------|
   | 新 session 恢复成功 | 继续检查 |
   | 新 session 恢复失败 | ALERT: RECOVERY_FAILED |
   | 恢复带 uncertainty | 记录日志，继续 |
   | 同 session 继续 | 跳过恢复处理 |

3. **恢复摘要**
   
   如果是新 session 且恢复成功，生成恢复摘要：
   ```bash
   if [ "$IS_NEW_SESSION" = "true" ] && [ "$RECOVERED" = "true" ]; then
       # 恢复摘要已由 session-start-recovery 生成到:
       # artifacts/session_recovery/latest_recovery_summary.md
       # 事件已记录到 state/session_continuity_events.jsonl
       :
   fi
   ```

4. **处理 uncertainty**
   
   ```bash
   if [ "$UNCERTAINTY" = "true" ]; then
       # uncertainty 已记录到事件日志
       # 不阻断 heartbeat，但记录日志
       echo "Recovery completed with uncertainty" >> /tmp/continuity.log
   fi
   ```

---

## State Flush Check (每次 heartbeat) ⭐⭐⭐⭐⭐

### 触发落盘检查

**检查是否有以下变化**:
- 任务状态变化
- 当前目标变化
- 分支/仓库状态变化
- 架构决策变化
- 下一步/blocker 变化

### Context 阈值行为

| Context | 行为 |
|---------|------|
| < 60% | 按事件触发写状态 |
| 60-80% | 每条实质性回复前检查并必要时写 |
| > 80% | 强制 handoff + 压缩前强制落盘 |

### 获取当前 context
```bash
session_status 2>/dev/null | grep -E "Context|Budget" || echo "unknown"
```

---

## Session Continuity Daily Check (每日一次) ⭐⭐⭐

### 触发条件
- 每天首次 heartbeat 时执行
- 通过 state/continuity_last_check 判断

### 执行脚本
```bash
~/.openclaw/workspace/tools/session-continuity-daily-check
```

### 记录指标
| 指标 | 来源 | 更新时机 |
|------|------|----------|
| recovery_success_count | session-start-recovery | 每次恢复成功 |
| handoff_count | handoff 生成 | 每次 handoff |
| high_context_count | pre-reply-guard | context > 80% |
| interruption_count | session-start-recovery | 恢复检测到中断 |
| uncertainty_count | session-start-recovery | uncertainty flag |
| conflict_count | session-start-recovery | conflict resolved |
| failure_count | session-start-recovery | 恢复失败 |
| wal_append_count | WAL 文件行数 | 每日检查 |

### 输出位置
- HEALTH_SUMMARY.md - 每日更新
- ROLLOUT_OBSERVATION.md - 事件追加

### 注意事项
- 此检查不影响 heartbeat 输出
- 仅在后台更新状态文件
- 失败不阻断 heartbeat

---

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

---

## Workflow health checks

重点关注：
- `pending_count`
- `receipt_age_p95`
- `stuck_claimed_count`

---

## Do not do in heartbeat
- 不启动新项目
- 不进行复杂业务判断
- 不长时间阻塞
- 不在心跳中向用户输出长解释
- 不跳过 Session Recovery Check
- 不跳过 State Flush Check
- 不跳过 Session Continuity Daily Check

---

## Output format

**正常情况**:
```
HEARTBEAT_OK
```

**需要恢复**:
```
ALERT: SESSION_RECOVERY_NEEDED
```

**恢复失败**:
```
ALERT: RECOVERY_FAILED
```

**需要落盘**:
```
HEARTBEAT_OK
[后台执行落盘，不输出]
```
