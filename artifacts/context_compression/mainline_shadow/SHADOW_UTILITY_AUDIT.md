# Shadow Utility Audit Report

**Audit Date**: 2026-03-07T05:19:00CST
**Observer**: Mainline Shadow Pipeline
**Result**: **D. Trigger Path Not Exercised**

---

## Executive Summary

**Why 0 Triggers?** 集成路径未真正接入主流程。

- SHADOW_MANIFEST.json 存在（文档）
- Feature flags 配置存在（文档）
- 但主流程中**没有实际调用** compression 工具

---

## Core Findings

### 1. 主流程会话存在

| Metric | Value |
|--------|-------|
| Current Session ID | 80c3d396-d180-415e-aada-ce7d6daf9dc2 |
| Session Started | 2026-03-07T09:34:51.621Z |
| Session Size | 475 KB |
| Tool Calls | 64 exec + 7 read |

**Status**: ✅ 主流程正常，会话在运行

### 2. Compression 工具调用：❌ 不存在

| Tool | Expected | Found |
|------|----------|-------|
| context-budget-check | Before prompt assemble | ❌ 0 calls |
| context-compress | On threshold | ❌ 0 calls |
| capsule-builder | During compression | ❌ 0 calls |
| context-retrieve | During recall | ❌ 0 calls |

**Status**: ❌ 集成点未接入

### 3. 实际调用的工具

```
exec:    64 calls
read:    7 calls
```

**Observation**: 只有标准工具调用，没有 compression 相关工具

---

## Root Cause Analysis

### 问题链

```
1. SHADOW_MANIFEST.json 定义了集成点 ✅
   └─ pre_prompt_assemble: context-budget-check
   
2. 但 OpenClaw 主流程代码没有实现这个集成 ❌
   └─ 没有在 prompt assemble 前调用 context-budget-check
   
3. 导致 budget check 从未执行 ❌
   └─ sessions_evaluated_by_budget_check = 0
   
4. 导致 threshold 判断从未发生 ❌
   └─ sessions_over_threshold = 0
   
5. 导致 shadow trigger 从未触发 ❌
   └─ shadow_trigger_count = 0
```

### 分类

**D. Trigger Path Not Exercised**

原因：集成点定义在文档中，但未在 OpenClaw 运行时代码中实现。

---

## Counters

### A. 会话层

| Counter | Value |
|---------|-------|
| observed_low_risk_sessions | 1 (current) |
| eligible_low_risk_sessions | 1 |
| sessions_skipped_by_scope_filter | 0 |

### B. 预算检查层

| Counter | Value |
|---------|-------|
| sessions_evaluated_by_budget_check | 0 |
| sessions_not_evaluated_by_budget_check | 1 |
| budget_check_error_count | 0 |

### C. 阈值层

| Counter | Value |
|---------|-------|
| sessions_over_threshold | N/A (never checked) |
| sessions_under_threshold | N/A (never checked) |
| threshold_value_used | N/A |

### D. 压缩机会层

| Counter | Value |
|---------|-------|
| compression_opportunity_count | 0 |
| compression_opportunity_missed_count | 0 |

### E. 触发层

| Counter | Value |
|---------|-------|
| shadow_trigger_count | 0 |
| trigger_blocked_by_condition_count | N/A |
| trigger_error_count | 0 |

### F. 安全性确认

| Counter | Value |
|---------|-------|
| real_reply_modified_count | 0 ✅ |
| active_session_pollution_count | 0 ✅ |

---

## Diagnostic Answers

| Question | Answer |
|----------|--------|
| 有 low-risk session 流入? | ✅ 是，当前会话就是 |
| 流入的 session 是否经过 budget check? | ❌ 否，budget check 从未调用 |
| budget check 结果如何? | N/A，从未执行 |
| 阈值设置如何? | N/A，从未判断 |
| scope/filter 是否过严? | N/A，前置步骤未执行 |
| 0 triggers 的原因? | 集成点未接入主流程 |

---

## Evidence

### Session Log 证据

```bash
# 实际工具调用
$ grep -o '"toolName":"[^"]*"' session.jsonl | sort | uniq -c
     64 "toolName":"exec"
      7 "toolName":"read"

# Compression 工具调用
$ grep '"toolName":"context-budget-check"' session.jsonl
# (无结果)

$ grep '"toolName":"context-compress"' session.jsonl
# (无结果)
```

### 配置检查

```bash
$ cat ~/.openclaw/config.json
# 文件不存在
```

---

## Conclusion

### 分类: D. Trigger Path Not Exercised

**原因**:
- SHADOW_MANIFEST.json 是文档，不是运行时配置
- OpenClaw 主流程代码没有实现集成点
- compression 工具从未被调用

**不是**:
- 不是流量不足（会话在运行）
- 不是阈值过高（从未检查）
- 不是 scope 过严（前置步骤未执行）

---

## Recommendation

### 3. Isolated Fix Recommended

**修复建议**:
1. 在 OpenClaw 主流程中实现集成点
2. 在 prompt assemble 前调用 context-budget-check
3. 当 threshold 达到时调用 context-compress --mode shadow

**注意**:
- 这需要修改 OpenClaw 核心代码
- 不是修改 patch set
- 需要单独评估和实现

---

## Next Steps

1. **评估集成实现**
   - 确定 OpenClaw 代码中添加集成点的位置
   - 评估实现复杂度

2. **不修改 patch set**
   - 保持 anchor-enhanced capsule 和 anchor-aware retrieve 冻结
   - 只修改集成层

3. **继续 shadow 观察**
   - 集成实现后重新开始观察窗口
   - 收集实际 shadow 数据

---

**Audit Completed**: 2026-03-07T05:19:00CST
