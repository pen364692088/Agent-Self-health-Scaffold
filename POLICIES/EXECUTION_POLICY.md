# Execution Policy Enforcement & Anti-Forgetting Framework v1.0

**Effective Date**: 2026-03-09
**Status**: ACTIVE
**Scope**: All tool operations affecting ~/.openclaw/**

---

## 1. Purpose

### 1.1 Problem Statement

解决"规则写进 SOUL.md/TOOLS.md 后仍被忘记"的根问题：

| 症状 | 根因 |
|------|------|
| 规则未执行 | 未进入工具选择链路 |
| 违规后无后果 | 只有事后解释，无事前阻断 |
| 同类问题重复 | 无记忆/升级机制 |

### 1.2 In Scope

- 敏感路径写入控制（~/.openclaw/**）
- 工具选择前的 policy 路由
- 违规阻断与替代方案
- Gate A/B/C 接入
- 违规记录与升级机制

### 1.3 Out of Scope

- 模型幻觉（模型层问题）
- 工具执行失败（基础设施问题）
- 业务逻辑判断（应用层问题）
- Prompt 注入防御（安全层问题）

---

## 2. Architecture

### 2.1 Four-Layer Model

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Declaration Layer (SOUL.md, POLICY docs)      │
│  - 规则定义、优先级、原因                                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Routing Layer (policy matcher)                │
│  - path + operation + tool → decision                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Enforcement Layer (deny/reroute/warn)         │
│  - 硬阻断、软告警、自动路由                              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Verification Layer (Gate/doctor/audit)        │
│  - 收尾验证、健康检查、审计日志                          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Decision Flow

```
Tool Call → Policy Matcher → Match Found?
                                ↓ Yes        ↓ No
                          Evaluate Rule    ALLOW
                                ↓
                          Decision: ALLOW / DENY / REROUTE / WARN
                                ↓
                          Action → Log → Return
```

---

## 3. Rule Types

### 3.1 Path + Tool Deny

```yaml
id: OPENCLAW_PATH_NO_EDIT
status: active
priority: P0
scope: path
trigger:
  path_pattern: "~/.openclaw/**"
  operation: write
  tool: edit
action: deny
fallback: "Use safe-write, safe-replace, or exec + heredoc"
```

### 3.2 Path + Tool Allowlist

```yaml
id: SENSITIVE_PATH_PREFER_SAFE_WRITE
status: active
priority: P1
scope: path
trigger:
  path_pattern: "~/.openclaw/**"
  operation: write
  tool: write
action: warn
fallback: "Prefer safe-write for atomic writes with verification"
```

### 3.3 Action Precondition Required

```yaml
id: PERSIST_BEFORE_REPLY
status: active
priority: P1
scope: action
trigger:
  action: reply
  state_change: true
action: warn
fallback: "Persist state to SESSION-STATE.md before replying"
```

### 3.4 Mandatory Gate Before Close

```yaml
id: GATE_REQUIRED_BEFORE_CLOSE
status: active
priority: P0
scope: action
trigger:
  action: task_close
action: deny
fallback: "Must call verify-and-close first"
```

### 3.5 Fragile Replace Block

```yaml
id: FRAGILE_REPLACE_BLOCK_ON_MANAGED_FILES
status: active
priority: P1
scope: path
trigger:
  path_pattern: "~/.openclaw/**/*.md"
  operation: replace
  tool: edit
action: deny
fallback: "Use safe-replace for managed files"
```

---

## 4. Enforcement Actions

### 4.1 DENY

硬阻断。工具调用被拒绝，返回固定错误消息。

```json
{
  "decision": "deny",
  "rule_id": "OPENCLAW_PATH_NO_EDIT",
  "reason": "~/.openclaw/** paths cannot use edit tool",
  "fallback": "Use safe-write, safe-replace, or exec + heredoc",
  "log_id": "violation_20260309_001"
}
```

### 4.2 REROUTE

自动路由到替代工具。

```json
{
  "decision": "reroute",
  "rule_id": "SENSITIVE_PATH_PREFER_SAFE_WRITE",
  "original_tool": "write",
  "reroute_to": "safe-write",
  "reason": "Sensitive path prefers safe-write"
}
```

### 4.3 WARN

告警但允许执行。记录到日志。

```json
{
  "decision": "warn",
  "rule_id": "PERSIST_BEFORE_REPLY",
  "message": "State should be persisted before reply",
  "log_id": "warning_20260309_001"
}
```

### 4.4 ALLOW

正常通过。

```json
{
  "decision": "allow",
  "rule_id": null,
  "message": "No policy violations detected"
}
```

---

## 5. Violation Handling

### 5.1 Severity Levels

| Level | Action | Examples |
|-------|--------|----------|
| P0 | DENY | Path + tool deny, Gate bypass |
| P1 | WARN → DENY (repeat) | Fragile replace, non-preferred tool |
| P2 | WARN only | Style violations |

### 5.2 Escalation

| Occurrence | Action |
|------------|--------|
| 1st | Log + WARN |
| 2nd | Log + Upgrade severity |
| 3rd | Log + Mandatory hardening candidate |

### 5.3 Rule Promotion

Rules can be promoted from documentation → warning → enforcement:

1. **Documentation Only**: New rule, no automation
2. **Warning Mode**: Log violations, no block
3. **Enforcement Mode**: Hard deny/allowlist

**Promotion Criteria**:
- Repeat violations ≥ 2 times
- Core path affected
- Delivery failure caused
- User explicit request

---

## 6. Gate Integration

### 6.1 Gate A (Contract)

- Rule boundaries clearly defined
- Extensible framework exists
- Not a temporary patch

### 6.2 Gate B (E2E)

- Behavior-level verification passed
- No false blocks
- Regression tests exist

### 6.3 Gate C (Preflight)

- Runtime integration complete
- Tests passing
- Audit visible

---

## 7. Tools Reference

| Tool | Purpose |
|------|---------|
| `policy-eval` | Evaluate tool call against policies |
| `policy-doctor` | Health check for policy system |
| `policy-violations-report` | Generate violation reports |
| `safe-write` | Atomic write with verification |
| `safe-replace` | Safe content replacement |

---

## 8. Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-09 | Initial framework creation |

