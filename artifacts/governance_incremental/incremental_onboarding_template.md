# 增量入口纳管模板

**版本**: 1.0.0
**创建时间**: 2026-03-16
**用途**: 新增入口的标准纳管模板

---

## 入口信息

| 字段 | 值 |
|------|-----|
| entry_id | entry-XXX |
| entry_path | tools/xxx |
| classification | P0/P1/P2/P3 |
| discovery_time | YYYY-MM-DDTHH:MM:SSZ |
| discoverer | auto/manual |

---

## 1. 边界确认

### 1.1 可执行性

- [ ] 是否真实可执行
- [ ] 是否有 shebang 或执行权限
- [ ] 是否有实际功能

### 1.2 主链影响

- [ ] 是否触发任务执行
- [ ] 是否影响任务决策
- [ ] 是否影响恢复/retry/resume
- [ ] 是否影响 Gate/放行

### 1.3 分类判定

- [ ] P0 - 主链强相关
- [ ] P1 - 潜在主链旁路
- [ ] P2 - 辅助治理
- [ ] P3 - 测试/示例/废弃

### 1.4 裁决结果

- [ ] register_now - 立即纳管
- [ ] register_after_fix - 修复后纳管
- [ ] exclude_non_mainline - 排除非主链
- [ ] exclude_dead_or_false_positive - 排除废弃/误报

---

## 2. Registry 登记

```yaml
- entry_id: "entry-XXX"
  entry_path: "tools/xxx"
  entry_type: "cli|daemon|script"
  class: "P0|P1|P2|P3"
  owner: "team-name"
  description: "入口描述"
  policy_bind_connected: true|false
  guard_connected: true|false
  hard_judge_connected: true|false
  boundary_checked: true|false
  preflight_covered: true|false
  ci_covered: true|false
  status: "active|pending_fix|deprecated"
  registered_at: "YYYY-MM-DDTHH:MM:SSZ"
```

---

## 3. 治理接入

### 3.1 接入状态

| 治理项 | 状态 | 说明 |
|--------|------|------|
| policy_bind_connected | ✅/❌ | 策略绑定 |
| guard_connected | ✅/❌ | 执行保护 |
| hard_judge_connected | ✅/❌/N/A | 硬判决 |
| boundary_checked | ✅/❌ | 边界检查 |
| preflight_covered | ✅/❌/N/A | 预检覆盖 |
| ci_covered | ✅/❌/N/A | CI 覆盖 |

### 3.2 缺口清单

| 缺口 | 影响 | 修复方案 |
|------|------|----------|
| xxx | xxx | xxx |

---

## 4. Gate 验收

### 4.1 Gate A: 契约验证

- [ ] 入口定义完整
- [ ] 字段类型正确
- [ ] 必填字段存在

**结果**: PASS/FAIL

### 4.2 Gate B: E2E 验证

- [ ] 入口可执行
- [ ] 治理接入有效
- [ ] 回调/日志正常

**结果**: PASS/FAIL

### 4.3 Gate C: 预检验证

- [ ] 边界检查通过
- [ ] 无安全隐患
- [ ] 资源限制合理

**结果**: PASS/FAIL

---

## 5. 处理结论

- [ ] ✅ 入口已完整纳管
- [ ] ⚠️ 需要修复后纳管
- [ ] ❌ 排除（非主链/废弃）

---

## 6. 审批

| 角色 | 姓名 | 时间 | 签名 |
|------|------|------|------|
| 发现人 | | | |
| 处理人 | | | |
| 审批人 | | | |

---

## 7. 附件

- 扫描结果: `artifacts/governance_incremental/entry_XXX_scan.json`
- 治理检查: `artifacts/governance_incremental/entry_XXX_governance.json`
- Gate 报告: `artifacts/governance_incremental/entry_XXX_gate.json`

---

**模板版本**: 1.0.0
**最后更新**: 2026-03-16
