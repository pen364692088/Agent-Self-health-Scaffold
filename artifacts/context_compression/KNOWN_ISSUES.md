# Context Compression Known Issues

**Last Updated**: 2026-03-06 11:56 CST

---

## Issue #1: context-retrieve L2 Parameter Error

**Status**: Known, Non-Blocking
**Priority**: P2
**Affects**: Gate 2 (L2 Vector Search)
**Does NOT Affect**: Gate 0, Gate 1, S1 (capsule-only)

### Problem

`context-retrieve` 调用 OpenViking 时使用了错误的参数 `-o json`：

```python
# 错误
['openviking', 'find', query, '--limit', str(limit), '-o', 'json']

# 正确
['openviking', 'find', query, '--limit', str(limit)]
# openviking find 默认输出 JSON，不需要 -o 参数
```

### Impact

- L2 (Vector Enhancement) 检索失败
- `context-retrieve --health` 返回 `degraded_but_functional`
- OpenViking 服务本身运行正常

### Root Cause

openviking CLI 参数变更，不再支持 `-o json`

### Fix Location

`tools/context-retrieve` 第 166 行

### Fix Type

单行修改，极小变更

### Blocker Status

**NOT A BLOCKER**

- S1 使用 `--capsule-only` 模式
- Gate 0 已通过（L1 可用）
- Gate 1 不依赖 L2
- 只影响 Gate 2 (Full Retrieval Ready)

### Resolution Timeline

**冻结到 S1 结束后**

修复时机：
1. S1 结束后统一修复
2. 或 S2 启动前作为 Gate 2 准备项

**不现在修复的原因**：
- 非 blocker
- 会污染 S1 证据
- S1 阶段重心是验证最小闭环

### Workaround

S1 使用 capsule-only 模式：

```bash
context-retrieve --capsule-only
```

---

## Issue Tracking

| Issue | Status | Priority | Gate | S1 Blocker |
|-------|--------|----------|------|------------|
| #1 L2 param error | Known | P2 | Gate 2 | No |

---

**Keywords**: `known-issue` `non-blocking` `gate-2-backlog` `feature-frozen`
