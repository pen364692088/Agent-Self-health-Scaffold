# Subagent Inbox 架构 v1.0

## 背景

**问题**：同步回传链路在父代理等待态下不稳定，导致超时/未送达风险。

**原因**：`sessions_send` 在 timeoutSeconds > 0 时会等待目标 run 完成，而父代理正在等待子代理完成，形成循环等待。

**解决**：改用持久化邮箱解耦结果投递与消费。

## 架构

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────┐
│   Parent    │         │   Mailbox        │         │   Child     │
│   Agent     │         │   (File System)  │         │   Agent     │
└──────┬──────┘         └────────┬─────────┘         └──────┬──────┘
       │                         │                          │
       │  spawn-with-callback    │                          │
       │─────────────────────────────────────────────────►  │
       │  (task_id, run_id)      │                          │
       │                         │                          │
       │                         │  subagent-inbox write    │
       │                         │◄─────────────────────────│
       │                         │  (原子写入 .done.json)    │
       │                         │                          │
       │  subagent-inbox check   │                          │
       │◄────────────────────────│                          │
       │  (轮询 pending)         │                          │
       │                         │                          │
       │  process → handler      │                          │
       │──┬──────────────────────│                          │
       │  │ .done → .claimed     │                          │
       │  │ handler 处理         │                          │
       │  │ .claimed → .processed│                          │
       │◄─┘                      │                          │
```

## 硬化点

### 1. 原子写入

```python
# 先写 .tmp
with open(tmp_file, 'w') as f:
    json.dump(receipt, f)
    f.flush()
    os.fsync(f.fileno())

# 再 rename
os.rename(tmp_file, target_file)
```

**防止**：读到半截文件

### 2. 幂等处理

状态机：`.done.json` → `.claimed.json` → `.processed.json`

```bash
# 处理前检查
if processed_file.exists() or claimed_file.exists():
    continue  # 跳过

# 认领
os.rename(done_file, claimed_file)

# 处理成功
os.rename(claimed_file, processed_file)
```

**防止**：重复处理同一回执

### 3. Schema v1 冻结

```json
{
  "task_id": "task_20260306_120000_a1b2c3d4",
  "run_id": "run_a1b2c3d4",
  "session_key": "agent:main:subagent:uuid",
  "parent_session_key": "agent:main:telegram:direct:8420019401",
  "status": "completed|failed|timeout",
  "summary": "任务摘要",
  "artifacts": [],
  "error": null,
  "notify_user": true,
  "written_at": "2026-03-06T12:00:00",
  "retry_count": 0,
  "metadata": {}
}
```

Schema 文件：`schemas/subagent_receipt.v1.schema.json`

### 4. 失败回执统一处理

```bash
# 成功
subagent-inbox write --task-id xxx --status completed --summary "..."

# 失败
subagent-inbox write --task-id xxx --status failed --summary "错误"

# 超时
subagent-inbox write --task-id xxx --status timeout --summary "超时"
```

### 5. 轮询架构

| 触发器 | 频率 | 用途 |
|--------|------|------|
| systemd worker | 5秒 | 主链路 |
| cron | 5分钟 | 兜底 |

## 工具

### spawn-with-callback v2.2

创建带回调指令的子代理任务：

```bash
spawn-with-callback "任务描述" -m qianfan-code-latest -t 300
```

### subagent-inbox v1.0

邮箱管理：

```bash
# 写入回执（子代理用）
subagent-inbox write --task-id xxx --run-id xxx --status completed --summary "..."

# 检查待处理（父代理用）
subagent-inbox check --once

# 处理回执
subagent-inbox process <task_id>

# 启动 worker（持续轮询）
subagent-inbox check --interval 5
```

### subagent-completion-handler v2.2

处理完成回执，推进工作流。

## 对比

| 特性 | sessions_send | 邮箱模式 v1.0 |
|------|--------------|---------------|
| 实时性 | 高（但会超时） | 低（轮询延迟 3-10s） |
| 可靠性 | ❌ 父代理等待态下失败 | ✅ 文件系统可靠 |
| 幂等性 | ❌ 需要额外实现 | ✅ 状态机保证 |
| 可审计 | ❌ 无持久化 | ✅ 文件可追溯 |
| 失败处理 | ❌ 静默丢失 | ✅ 统一处理 |

## 回归测试

```bash
# 运行测试
python3 ~/.openclaw/workspace/tests/test_subagent_inbox.py
```

测试覆盖：
1. happy path: completed → claimed → processed
2. failed/timeout path: 能统一进入 handler
3. duplicate receipt: 不会重复推进两次

## 监控指标

| 指标 | 描述 | 告警阈值 |
|------|------|---------|
| pending_count | 待处理回执数 | >10 持续 5 分钟 |
| receipt_age_p95 | 回执等待时间 P95 | >60s |
| stuck_claimed_count | 认领但未处理的回执 | >0 持续 10 分钟 |

## 服务管理

```bash
# 查看状态
systemctl --user status subagent-inbox-worker

# 启动/停止
systemctl --user start subagent-inbox-worker
systemctl --user stop subagent-inbox-worker

# 查看日志
journalctl --user -u subagent-inbox-worker -f
```

## 未来演进

当 OpenClaw 提供稳定的 parent-trigger completion 时（如 `announceTarget="parent"`），可以考虑简化邮箱模式。

但目前邮箱模式 v1.0 是生产可用的方案。

---

## Worker 语义

### 单实例保证

**当前设计：单实例**

通过 `flock(LOCK_EX | LOCK_NB)` 确保全局只有一个 worker 在处理：

```python
if not self.acquire_lock(timeout=5):
    # 另一个 worker 正在运行，跳过
    time.sleep(interval)
    continue
```

**为什么单实例**：
1. 避免同一回执被多个 worker 同时处理
2. 文件 claim 不支持跨进程原子操作
3. 简化幂等逻辑

### 多实例支持（未来）

如果需要高可用多实例，需要：

1. **分布式锁**：Redis / etcd / 文件锁
2. **原子 claim**：使用 `link()` 或 `rename()` 的原子性
3. **任务分片**：每个 worker 处理不同的 task_id 范围

**当前不支持**：启动多个 worker 进程会互相争抢锁，效率降低。

---

## 状态机完整定义

```
┌──────────┐     claim      ┌──────────┐     process    ┌───────────┐
│  .done   │ ────────────► │ .claimed │ ────────────► │ .processed│
└──────────┘               └──────────┘               └───────────┘
     ▲                           │
     │                           │ timeout (5min)
     │                           ▼
     │                    ┌──────────┐
     └────────────────────│  requeue │
                          └──────────┘
                                │
                                │ retry > 3
                                ▼
                          ┌──────────┐
                          │  .stale  │
                          └──────────┘
```

### 状态转换规则

| 当前状态 | 条件 | 目标状态 |
|---------|------|---------|
| .done | worker claim | .claimed |
| .claimed | handler success | .processed |
| .claimed | handler fail | .done (rollback) |
| .claimed | timeout + retry < 3 | .done (requeue) |
| .claimed | timeout + retry >= 3 | .stale |
| .processed | age > 7 days | deleted |
| .stale | age > 7 days | deleted |

---

## Retention 策略

| 状态 | 保留时间 | 原因 |
|------|---------|------|
| .processed (completed) | 7 天 | 审计需求 |
| .processed (failed/timeout) | 30 天 | 问题排查 |
| .stale | 7 天 | 人工介入记录 |

### 清理命令

```bash
# 手动清理
subagent-inbox cleanup --retention-days 7

# 建议 cron（每天凌晨）
0 0 * * * ~/.openclaw/workspace/tools/subagent-inbox cleanup
```

---

## sessions_send 定位

### 正式定位

**sessions_send**：仅用于非关键通知/调试，**不应用于关键完成回执**。

**原因**：
- 同步回传链路在父代理等待态下不稳定
- 超时/未送达风险
- 无持久化，不可审计

### 替代方案

| 场景 | 推荐方案 |
|------|---------|
| 子代理完成回执 | ✅ subagent-inbox |
| 轻量状态通知 | sessions_send |
| 调试日志 | sessions_send / console |
| 关键结果传递 | ✅ subagent-inbox |

### 迁移指南

```bash
# 旧方式（已废弃）
sessions_send(sessionKey="parent", message='{"type":"subagent_done",...}')

# 新方式
subagent-inbox write --task-id xxx --run-id xxx --status completed --summary "..."
```

---

## Production-Beta 准入标准

当前状态：**production-beta**

### 已验证

- [x] 原子写入
- [x] 幂等处理（状态机）
- [x] 失败回执统一处理
- [x] Worker 单实例
- [x] Claimed 超时回收
- [x] Retention 清理
- [x] 回归测试 3 条

### 待验证（24h soak）

- [ ] pending_count 不长期堆积
- [ ] receipt_age_p95 不随时间飘高
- [ ] stuck_claimed_count 偶发上升能自动恢复
- [ ] worker 重启后自动恢复处理
- [ ] 真实 Telegram 多任务场景

### 升正式标准

1. 24h soak 通过
2. 真实场景验证（≥10 个子代理任务）
3. 无 P0/P1 问题
