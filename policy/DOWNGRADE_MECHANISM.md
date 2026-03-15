# 降级/冻结机制说明

## 版本: 1.0
## 生效日期: 2026-03-15

---

## 1. 降级触发条件

### 1.1 自动降级触发

| 条件 | 阈值 | 降级动作 |
|-----|------|---------|
| 连续违规 | 2 次 | 降级一级 |
| 修改高保护区 | 1 次 | 立即降级到 L0 |
| 将 SKIP 伪装为 PASS | 1 次 | 降级一级 |
| 将缺失伪装为通过 | 1 次 | 降级一级 |
| 自判通过 | 1 次 | 降级一级 |

### 1.2 违规类型定义

```yaml
violations:
  critical:
    - modify_protected_zone      # 修改高保护区
    - self_judgment              # 自判通过
    - skip_as_pass               # SKIP 伪装 PASS
    
  major:
    - gate_change_in_repair_pr   # 修复 PR 改 Gate
    - relax_gate_without_cause   # 无根因放宽 Gate
    - missing_as_pass            # 缺失伪装通过
    
  minor:
    - unclear_skip_reason        # SKIP 原因不清
    - missing_audit_log          # 缺失审计日志
```

---

## 2. 降级级别

```
L3 (受限自动合入) 
    ↓ 降级
L2 (修复分支提交)
    ↓ 降级
L1 (沙箱修复)
    ↓ 降级
L0 (观察/人工审查)
```

### 2.1 各级别权限

| 级别 | 自动执行 | 合入主链 | 修改高保护区 |
|-----|---------|---------|-------------|
| L3 | ✅ | ✅ (通过所有 Gate) | ❌ |
| L2 | ✅ | ❌ (仅创建 PR) | ❌ |
| L1 | ✅ (沙箱内) | ❌ | ❌ |
| L0 | ❌ | ❌ | ❌ |

---

## 3. 降级流程

### 3.1 自动降级

```
违规检测
    ↓
记录违规事件到 policy/violations.yaml
    ↓
检查连续违规次数
    ↓
触发降级
    ↓
更新当前级别
    ↓
通知管理员
    ↓
冻结自动修复 (L0)
```

### 3.2 降级记录格式

```yaml
# policy/violations.yaml
downgrades:
  - timestamp: "2026-03-15T02:30:00Z"
    from_level: "L2"
    to_level: "L1"
    reason: "连续 2 次将 SKIP 伪装为 PASS"
    violations:
      - id: "v-001"
        type: "skip_as_pass"
        timestamp: "2026-03-15T02:15:00Z"
        evidence: "artifacts/violations/v-001.json"
      - id: "v-002"
        type: "skip_as_pass"
        timestamp: "2026-03-15T02:20:00Z"
        evidence: "artifacts/violations/v-002.json"
    auto_recovery: false
    requires_manual_approval: true
```

---

## 4. 恢复流程

### 4.1 自动恢复条件

- 连续 5 次修复无违规
- 所有 Gate 通过
- 审计日志完整

### 4.2 人工恢复

- 提交恢复申请 PR
- 说明违规根因已修复
- 通过 CODEOWNERS 审批

---

## 5. 冻结机制

### 5.1 立即冻结条件

- 修改 policy/ 目录
- 修改 contracts/ 目录
- 修改 validation/ 目录
- 修改 .github/workflows/gate*

### 5.2 冻结状态

```yaml
freeze:
  status: frozen
  reason: "修改高保护区: policy/gates.yaml"
  triggered_at: "2026-03-15T02:30:00Z"
  triggered_by: "auto-remediation"
  requires_action: "manual_review"
  contact: "@moonlight @admin"
```

---

## 6. 审计要求

所有降级/冻结事件必须记录:

1. 触发时间
2. 触发原因
3. 违规证据
4. 降级前后级别
5. 恢复条件
6. 审批记录

---

## 7. 通知机制

| 事件 | 通知方式 | 接收人 |
|-----|---------|--------|
| 降级 | GitHub Issue + Telegram | CODEOWNERS |
| 冻结 | GitHub Issue + Telegram | CODEOWNERS |
| 恢复申请 | GitHub PR | CODEOWNERS |
| 连续违规预警 | Telegram | CODEOWNERS |
