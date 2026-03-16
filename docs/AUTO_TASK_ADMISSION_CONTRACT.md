# Auto Task Admission Contract

**Version**: 1.0.0-draft
**Status**: Draft
**Date**: 2026-03-16

---

## Purpose

定义什么输入可以自动入任务，什么需要人工确认。

---

## Scope

适用范围：用户输入 → 任务队列

---

## Admission Rules

### R0: 只读分析（自动执行）

**行为**: 自动入任务，无需确认

**条件**:
- 只读操作
- 无副作用
- 无外部依赖

**示例**:
- 查询状态
- 分析代码
- 生成报告

### R1: 可逆写操作（自动执行 + checkpoint）

**行为**: 自动入任务，必须 checkpoint

**条件**:
- 可逆操作
- 有回滚路径
- 本地修改

**示例**:
- 创建文件
- 修改配置（有备份）
- 本地测试

### R2: 中风险修改（preflight + rollback plan）

**行为**: 自动入任务，但必须：
- Preflight 检查通过
- 有 rollback plan
- Contract 校验通过

**条件**:
- 可能影响多个文件
- 需要外部资源
- 有失败风险

**示例**:
- 多文件重构
- 依赖更新
- 配置迁移

### R3: Destructive / 不可逆（强制人工确认）

**行为**: 不自动入任务，必须人工确认

**条件**:
- 不可逆操作
- 外部真实副作用
- 系统级变更
- 数据删除

**示例**:
- 删除数据
- 发布到生产
- 修改系统配置
- 外部 API 调用

---

## Dedup & Idempotency

### Dedup Rules

1. 相同输入在 24h 内不重复入任务
2. 任务 ID 基于 content hash
3. 已完成任务不重复入队

### Idempotency

1. 任务执行必须幂等
2. 相同输入 → 相同结果
3. 重复执行无副作用

---

## Task Queue

### Priority

| Priority | Type | Behavior |
|----------|------|----------|
| P0 | Critical | Immediate execution |
| P1 | High | Next available slot |
| P2 | Normal | Queue normally |
| P3 | Low | Background execution |

### Queue Limits

- Max concurrent tasks: 10
- Max queue size: 100
- Queue timeout: 24h

---

## Blocking Conditions

以下情况不自动入任务：

1. R3 级别操作
2. 缺少必要参数
3. 依赖未满足
4. 系统负载过高
5. 连续失败 ≥ 3 次

---

## Evidence Requirements

每次入任务必须记录：

1. 输入来源
2. 风险等级
3. Admission 决策
4. 时间戳
5. 任务 ID

---

## Verification

### Gate A: Admission Gate

- [ ] Risk level 正确分类
- [ ] Dedup 检查通过
- [ ] Queue 成功入队
- [ ] Evidence 记录完整

### Success Criteria

- Admission decision ≤ 100ms
- No false R3 admission
- No duplicate tasks

---

## Appendix

### Related Documents

- GATE_RULES.md
- AUTONOMY_CAPABILITY_BOUNDARY.md
- failure_taxonomy.yaml

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0-draft | 2026-03-16 | Initial draft |
