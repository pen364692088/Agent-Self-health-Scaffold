# Workflow Auto-Advance Policy v1.0

**让任何工作流自动推进、可观测、可控、可停机、可复盘。**

---

## 1. 术语定义

| 术语 | 定义 |
|------|------|
| **Event** | 完成事件，表示某个 step 已执行完毕，需要推进到下一步 |
| **Workflow** | 工作流，由多个 step 组成的有向无环图（DAG） |
| **Step** | 步骤，工作流的最小执行单元 |
| **Advance** | 推进，从当前 step 推进到下一个 step |
| **Inflight** | 推进中标记，表示推进正在进行，防止重复推进 |
| **Processed** | 已处理标记，表示推进已完成，幂等保证 |

---

## 2. 事件语义

### 完成事件必须包含

```json
{
  "run_id": "string (required)",
  "workflow_id": "string (optional)",
  "timestamp": "ISO8601 (auto-generated)",
  "status": "success|failed|timeout (optional)"
}
```

### 事件入队

```bash
event-queue enqueue <run_id> [--workflow-id <id>]
```

### 安全约束

- `run_id` 白名单: `[a-zA-Z0-9_-]+`
- 最大长度: 100 字符
- 防注入: 不允许 `/`, `\`, `..`, 空格等特殊字符

---

## 3. 幂等语义

### 重复事件安全

**保证**: 同一 `run_id` 多次入队只会推进一次

**实现**:
- 入队去重: 1 秒窗口内相同 run_id 只保留一次
- inflight 标记: 推进中拒绝重复推进
- processed 标记: 推进完成后拒绝重复

### 并发触发安全

**保证**: 多个进程/线程同时触发，只有一个成功

**实现**:
- 文件锁: `fcntl.flock()` 互斥锁
- 原子写入: temp → fsync → rename

---

## 4. 两阶段提交

### 推进流程

```
┌─────────────────────┐
│ 阶段 1: 写 inflight │
│ {"nonce": "...",   │
│  "at": "ISO",      │
│  "by": "worker"}   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 阶段 2: 调用 spawn │
│ sessions_spawn(...)│
└──────────┬──────────┘
           │
           ├─ 成功 → 清除 inflight + 写入 processed
           │
           └─ 失败 → 清除 inflight + 保留 processed=false
```

### 强约束

1. **必须先写 inflight**: 防止崩溃后无法恢复
2. **spawn 成功才能写 processed**: 保证一致性
3. **原子写入**: 所有状态更新必须 temp → fsync → rename

---

## 5. 锁与原子写

### 文件锁

- 锁文件: `WORKFLOW_STATE.json.lock` 或 `.workflow.lock`
- 实现: `fcntl.flock(fd, LOCK_EX)`
- 范围: 整个 WORKFLOW_STATE 文件

### 原子写入

```python
# 所有状态更新必须使用此模式
temp_file = WORKFLOW_FILE.with_suffix('.tmp')
with open(temp_file, 'w') as f:
    json.dump(state, f)
    f.flush()
    os.fsync(f.fileno())
temp_file.rename(WORKFLOW_FILE)  # 原子操作
```

---

## 6. 护栏

### 限速

| 护栏 | 默认值 | 说明 |
|------|--------|------|
| `MAX_ADVANCES_PER_HOUR` | 100 | 每小时最大推进次数 |
| `MAX_ADVANCES_PER_WORKFLOW` | 50 | 每个 workflow 最大推进次数 |
| `RATE_LIMIT_PER_SEC` | 5 | 每秒最大推进次数 |

### 并发上限

| 护栏 | 默认值 | 说明 |
|------|--------|------|
| `MAX_GLOBAL_INFLIGHT` | 10 | 全局最大并发 spawn |

### 退避

- 基础退避: 2 秒
- 指数退避: `backoff = base * 2^attempts`
- 最大重试: 3 次

### 卡死检测

- Running 超时: 600 秒（10 分钟）
- Inflight 超时: 60 秒
- 检测间隔: 每个 worker tick

---

## 7. 可观测指标

### 指标定义（校准后）

| 指标 | 定义 | 计算方式 |
|------|------|---------|
| **queue_wait_ms** | 队列等待时间 | `t_dequeue - t_enqueue` |
| **advance_exec_ms** | 推进执行时间 | `t_spawn_ok - t_dequeue` |
| **e2e_ms** | 端到端延迟 | `t_spawn_ok - t_enqueue` |
| **spawn_ms** | Spawn 内部耗时 | spawn backend 内部计时 |

### 时间点定义

- `t_enqueue`: 事件入队时间（event-queue 写入）
- `t_dequeue`: 事件被消费时间（worker 取出）
- `t_spawn_ok`: Spawn 成功返回时间

### 外部 SLA

- **e2e_ms** 是外部 SLA（用户体验）
- **spawn_ms** 只是组件耗时（内部诊断）

### 指标查询

```bash
callback-handler-auto --metrics
```

---

## 8. 应急流程

### Kill-switch 三种方式

| 方式 | 命令 |
|------|------|
| 文件开关 | `touch ~/.openclaw/workspace/STOP_AUTO_ADVANCE` |
| 环境变量 | `export AUTO_ADVANCE_ENABLED=0` |
| CLI | `callback-handler-auto --kill-switch` |

### 恢复运行

```bash
# 删除停止文件
rm ~/.openclaw/workspace/STOP_AUTO_ADVANCE

# 或 CLI
callback-handler-auto --unkill

# 重启服务
systemctl --user start callback-worker
```

### 应急流程（三步）

1. **先停**: 启用 kill-switch，防止继续扩大影响
2. **取证**: 收集日志、指标、状态文件
3. **恢复**: 排障后 --unkill，观察指标回稳

---

## 9. 兜底扫描归因

### fallback_reason 枚举

| 值 | 说明 |
|------|------|
| `event_missing` | 事件未入队，纯兜底 |
| `state_lag` | 事件先到但 state 未落盘，短退避重试 |
| `backoff_expired` | backoff_until 到期后立即尝试 |
| `startup_sweep` | Worker 启动时的初始扫描 |
| `opportunistic` | 队列空闲时的机会性扫描 |
| `manual_once` | 手动触发 `--once` |

### 日志输出

```
[fallback] reason=event_missing step=step_a run_id=xxx
```

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-05 | 初始版本，包含完整护栏和指标拆分 |

