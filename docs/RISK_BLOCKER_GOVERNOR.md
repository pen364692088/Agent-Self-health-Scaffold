# Risk Blocker Governor

**Version**: 1.0.0-draft
**Status**: Draft
**Date**: 2026-03-16

---

## Purpose

识别高风险动作，自动升级 blocker，防止未授权执行。

---

## Risk Classification

### R0: 只读分析（自动执行）

**定义**: 只读、无副作用、无外部依赖

**行为**:
- ✅ 自动执行
- ✅ 无需确认
- ✅ 无需 checkpoint

**示例**:
- 读取文件
- 查询状态
- 分析代码
- 生成报告

---

### R1: 可逆写操作（自动执行 + checkpoint）

**定义**: 可逆、有回滚路径、本地修改

**行为**:
- ✅ 自动执行
- ✅ 必须有 checkpoint
- ⚠️ 需要备份

**示例**:
- 创建文件
- 修改配置（有备份）
- 本地测试
- 临时文件操作

---

### R2: 中风险修改（preflight + rollback plan）

**定义**: 多文件影响、需要外部资源、有失败风险

**行为**:
- ⚠️ Preflight 检查
- ⚠️ Rollback plan
- ⚠️ Contract 校验

**Pre-flight Checklist**:
- [ ] 资源可用
- [ ] 依赖满足
- [ ] Rollback plan 存在
- [ ] 备份完成

**示例**:
- 多文件重构
- 依赖更新
- 配置迁移
- 数据迁移

---

### R3: Destructive / 不可逆（强制人工确认）

**定义**: 不可逆、外部真实副作用、系统级变更、数据删除

**行为**:
- ❌ 不自动执行
- ❌ 必须人工确认
- ❌ 必须记录审批

**示例**:
- 删除数据
- 发布到生产
- 修改系统配置
- 外部 API 调用（真实副作用）
- 数据库 schema 变更

---

## Blocker Detection

### Blocker Types

| Type | Severity | Action |
|------|----------|--------|
| Missing dependency | High | Pause + notify |
| Resource unavailable | Medium | Retry + escalate |
| R3 action detected | Critical | Block + require approval |
| Gate failure | Critical | Block + manual review |
| State inconsistent | Critical | Block + recover |

### Blocker Escalation

```
Blocker detected
    │
    ├─► R0/R1 blocker → Auto retry (max 3)
    │
    ├─► R2 blocker → Auto escalate + notify
    │
    └─► R3 blocker → Block immediately + require human
```

---

## Escalation Rules

### Automatic Escalation

以下情况自动升级：

1. Retry 失败 ≥ 3 次
2. R2 操作无 rollback plan
3. R3 操作未授权
4. Gate A/B/C 失败
5. State 不一致

### Escalation Process

```
1. Detect escalation trigger
2. Classify severity
3. Determine escalation path
4. Notify relevant parties
5. Wait for resolution
6. Resume or abort
```

---

## True Blocker Definition

**True Blocker**（真正无解的 blocker）:

满足以下条件之一：
1. R3 操作被拒绝
2. 关键依赖永久不可用
3. 外部系统故障且无 fallback
4. 用户明确取消
5. 超过 max retry + max replan

**Not True Blocker**（普通不确定性）:
- 临时资源不足
- 网络超时
- API rate limit
- 配置缺失（可补充）

---

## Approval Flow

### R3 Approval Process

```
1. R3 action detected
2. Generate approval request
3. Send to approver
4. Wait for response (timeout: 24h)
5. If approved → Execute with audit
6. If rejected → Abort + notify
7. If timeout → Escalate to admin
```

### Approval Evidence

- [ ] Approval request
- [ ] Approver identity
- [ ] Approval timestamp
- [ ] Execution audit log

---

## Emergency Stop

### Emergency Stop Triggers

1. 连续 R3 违规 ≥ 3 次
2. 系统资源耗尽
3. 安全审计失败
4. 用户明确停止

### Emergency Stop Process

```
1. Detect trigger
2. Stop all running tasks
3. Preserve state
4. Generate incident report
5. Notify admin
```

---

## Evidence Requirements

### Governance Evidence

- [ ] Risk classification log
- [ ] Blocker log
- [ ] Escalation log
- [ ] Approval log (for R3)
- [ ] Emergency stop log (if any)

---

## Appendix

### Related Documents

- AUTONOMY_CAPABILITY_BOUNDARY.md
- AUTO_TASK_ADMISSION_CONTRACT.md
- GATE_RULES.md

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0-draft | 2026-03-16 | Initial draft |
