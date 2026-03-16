# Phase E: 增量例外与过期回收报告

**执行时间**: 2026-03-16T23:15:00Z
**状态**: ✅ 完成

---

## 1. 目标

建立增量例外与过期回收机制，防止例外变成常态旁路。

---

## 2. 例外机制设计

### 2.1 例外注册表

**位置**: `contracts/governance_exceptions.yaml`

**结构**:
```yaml
schema_version: "1.0"
exceptions:
  - exception_id: "EXC-001"
    entry_id: "entry-XXX"
    exception_type: "missing_hard_judge"
    reason: "具体原因"
    owner: "team-name"
    created_at: "YYYY-MM-DDTHH:MM:SSZ"
    expires_at: "YYYY-MM-DDTHH:MM:SSZ"
    compensation: "补偿控制措施"
    status: "active|expired|resolved"
```

### 2.2 例外要求

| 要求 | 说明 |
|------|------|
| 必须关联 entry_id | 不能创建无主例外 |
| 必须有到期时间 | 不允许永久例外 |
| 必须有 owner | 必须有人负责 |
| 必须有补偿控制 | 不能无保护例外 |

---

## 3. 当前例外状态

### 3.1 已存在的例外

| exception_id | entry_id | 类型 | 状态 | 到期时间 |
|--------------|----------|------|------|----------|
| EXC-001 | entry-003 | missing_guard/boundary | active | 待设定 |
| EXC-002 | entry-015 | not_executable | active | 待设定 |
| EXC-003 | entry-016 | missing_guard/boundary | active | 待设定 |

### 3.2 例外分析

**entry-003 (auto-resume-orchestrator)**:
- 类型: missing_guard, missing_boundary, missing_hard_judge
- 原因: P0 入口，待补齐治理接入
- 建议: 限期 7 天内补齐

**entry-015 (resume_readiness_calibration.py)**:
- 类型: not_executable, missing_guard, missing_boundary
- 原因: Python 脚本，可通过 python 运行
- 建议: 可接受，标记为 script 类型

**entry-016 (resume_readiness_evaluator_v2.py)**:
- 类型: missing_guard, missing_boundary
- 原因: Python 脚本，待补齐
- 建议: 限期 7 天内补齐

---

## 4. 过期回收机制

### 4.1 检查频率

- 每日检查例外状态
- 到期前 3 天发送提醒
- 到期后自动升级

### 4.2 回收流程

```
检查到期 → 发送提醒 → 到期升级 → 强制处理 → 验证关闭
```

### 4.3 升级规则

| 情况 | 处理 |
|------|------|
| 到期前 3 天 | 发送提醒给 owner |
| 到期当天 | 标记为 expired，升级告警 |
| 过期 1 天 | Level 2 告警 |
| 过期 3 天 | Level 3 告警 + 阻断 |

---

## 5. 建议

### 5.1 设定到期时间

```yaml
exceptions:
  - exception_id: "EXC-001"
    expires_at: "2026-03-23T23:59:59Z"  # 7 天后
  - exception_id: "EXC-002"
    expires_at: "2026-04-16T23:59:59Z"  # 30 天后（可接受）
  - exception_id: "EXC-003"
    expires_at: "2026-03-23T23:59:59Z"  # 7 天后
```

### 5.2 建立例外监控

```bash
# 每日检查例外
python tools/governance-exception-check --daily
```

---

## 6. 交付物

| 产物 | 路径 |
|------|------|
| 例外审查报告 | artifacts/governance_incremental/exception_review_report.md |

---

**交付人**: Manager (Coordinator AI)
**交付时间**: 2026-03-16T23:15:00Z
