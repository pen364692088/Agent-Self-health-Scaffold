# State Concurrency Policy v1.1

## Overview

本文档定义了状态文件的并发访问策略，防止多 agent / 多进程写入冲突。

## Protected Files

| 文件 | 保护级别 | 锁超时 |
|------|----------|--------|
| SESSION-STATE.md | 必须加锁 | 30s |
| working-buffer.md | 必须加锁 | 30s |
| handoff.md | 必须加锁 | 30s |
| WAL journal | Append-only | 无需锁 |

## Locking Mechanism

### Lock File Location
```
state/locks/<filename>.lock
```

### Lock File Format
```json
{
  "owner": "telegram:8420019401",
  "timestamp": "2026-03-07T18:00:00-06:00",
  "timestamp_unix": 1709854800.0,
  "file": "/path/to/SESSION-STATE.md"
}
```

### Lock Lifecycle

```
┌─────────────────────────────────────────────┐
│               Acquire Lock                   │
│         state-lock --acquire                │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│            Perform Operations               │
│         (read/write state files)            │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│               Release Lock                   │
│         state-lock --release                │
└─────────────────────────────────────────────┘
```

## Stale Lock Detection

锁超过 **5 分钟** 未更新视为 stale，可以被其他进程清理。

```python
def is_lock_stale(lock_info: Dict) -> bool:
    age = time.time() - lock_info.get("timestamp_unix", 0)
    return age > 300  # 5 minutes
```

## Conflict Handling

### Scenario 1: Lock Already Held

```
Process A: acquire_lock(SESSION-STATE.md) → success
Process B: acquire_lock(SESSION-STATE.md) → wait or timeout
```

**处理**:
- 等待锁释放（默认 30s 超时）
- 或检测到 stale lock 后强制获取

### Scenario 2: Write Without Lock

```
Process A: write SESSION-STATE.md (no lock)
Process B: write SESSION-STATE.md (no lock)
```

**结果**: 可能互相覆盖，数据丢失

**解决**: 强制要求所有写入使用 `state-write-atomic` 工具

### Scenario 3: Concurrent WAL Append

```
Process A: append to WAL
Process B: append to WAL
```

**处理**: WAL 是 append-only，操作系统保证顺序写入安全

## Best Practices

### 1. Always Use Atomic Write

```bash
# ✅ 正确
state-write-atomic --file SESSION-STATE.md --content "<content>"

# ❌ 错误
echo "<content>" > SESSION-STATE.md
```

### 2. Lock Before Multi-File Update

```bash
# 更新多个文件前先加锁
state-lock --file SESSION-STATE.md --acquire
state-lock --file working-buffer.md --acquire

# 执行更新
state-write-atomic --file SESSION-STATE.md --content "..."
state-write-atomic --file working-buffer.md --content "..."

# 释放锁
state-lock --file SESSION-STATE.md --release
state-lock --file working-buffer.md --release
```

### 3. Use --with for Atomic Operations

```bash
# 在持有锁期间执行命令
state-lock --file SESSION-STATE.md --with "state-write-atomic --file SESSION-STATE.md --content '...'"
```

## Tools

### state-lock

```bash
# 获取锁
state-lock --file SESSION-STATE.md --acquire

# 检查锁状态
state-lock --file SESSION-STATE.md --check

# 释放锁
state-lock --file SESSION-STATE.md --release

# 持有锁执行命令
state-lock --file SESSION-STATE.md --with "<command>"
```

## Monitoring

### Check for Stale Locks

```bash
# 列出所有锁
ls state/locks/

# 检查特定锁
state-lock --file SESSION-STATE.md --check
```

### Lock Metrics

| 指标 | 描述 |
|------|------|
| locks_acquired | 成功获取锁次数 |
| locks_released | 成功释放锁次数 |
| lock_timeouts | 获取锁超时次数 |
| stale_locks_cleaned | 清理的过期锁数量 |

---
Version: 1.1
Created: 2026-03-07