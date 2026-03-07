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

1. **检测是否是新 session**
   - 比较 session ID 与上次记录
   - 如果是新 session，执行恢复流程

2. **新 session 恢复流程**:
   ```bash
   # 读取状态文件
   cat ~/.openclaw/workspace/SESSION-STATE.md
   cat ~/.openclaw/workspace/memory/working-buffer.md
   ls -t ~/.openclaw/workspace/handoff.md 2>/dev/null | head -1 | xargs cat
   ```

3. **验证恢复状态**
   - 与当前 repo/task 状态比较
   - 如有冲突，以文件/repo 为准
   - 报告状态不确定

4. **如果状态文件缺失或过期**
   - 从 git log / session index 重建
   - 报告 "SESSION_RECOVERY_NEEDED"

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

### 落盘动作

如果需要落盘:
```bash
# 更新 SESSION-STATE.md
cat > ~/.openclaw/workspace/SESSION-STATE.md << 'STATE'
# Session State

**Updated**: $(date -Iseconds)

## Current Objective
[当前目标]

## Current Phase
[当前阶段]

## Current Branch / Workspace
[当前分支/仓库]

## Latest Verified Status
[已确认状态]

## Next Actions
[下一步]

## Blockers
[阻塞项]
STATE

# 更新 working-buffer.md
cat > ~/.openclaw/workspace/memory/working-buffer.md << 'BUFFER'
# Working Buffer

**Updated**: $(date -Iseconds)

## Active Focus
[当前焦点]

## Hypotheses
[假设]

## Pending Verification
[待验证]
BUFFER
```

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

**需要落盘**:
```
HEARTBEAT_OK
[后台执行落盘，不输出]
```