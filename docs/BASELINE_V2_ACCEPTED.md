# Checkpointed Step Loop v2 - Accepted Baseline

## 冻结状态

**状态**: ✅ FROZEN  
**冻结日期**: 2026-03-15  
**冻结版本**: v2.0.0

---

## 冻结对象

本基线冻结以下已验证能力：

### 1. 单真实任务闭环
- 任务 ID: `pilot_docs_index_v2`
- 类型: 文档索引生成
- 步骤数: 4 (分析 → 创建 → 验证 → 收口)
- 真实产出: `docs/INDEX.md`

### 2. 中断恢复能力
- 已验证: 恢复后已成功步骤不重复执行
- attempts 跟踪正确
- lease 机制有效

### 3. Completion Gate 保护
- Gate A/B/C 全部通过
- 只基于 truth/evidence 放行
- 禁止假完成

### 4. 公开证据三件套
- `SUMMARY.md` - 任务总结
- `gate_report.json` - Gate 验证报告
- `receipt.json` - 完成收据

---

## 关键证据路径

| 类型 | 路径 | 验证状态 |
|------|------|----------|
| 任务目录 | `artifacts/tasks/pilot_docs_index_v2/` | ✅ |
| SUMMARY.md | `artifacts/tasks/pilot_docs_index_v2/final/SUMMARY.md` | ✅ |
| gate_report.json | `artifacts/tasks/pilot_docs_index_v2/final/gate_report.json` | ✅ |
| receipt.json | `artifacts/tasks/pilot_docs_index_v2/final/receipt.json` | ✅ |
| task_state.json | `artifacts/tasks/pilot_docs_index_v2/task_state.json` | ✅ |
| ledger.jsonl | `artifacts/tasks/pilot_docs_index_v2/ledger.jsonl` | ✅ |
| 真实产出 | `docs/INDEX.md` | ✅ |

---

## 必须长期保持的行为

### 执行能力
1. ✅ 真实 shell 命令可执行
2. ✅ 文件创建/修改可执行
3. ✅ 目录分析可执行
4. ✅ 输出验证可执行

### 恢复能力
1. ✅ 中断后可从持久化状态恢复
2. ✅ 已成功步骤不重复执行
3. ✅ lease 过期后可 reclaim

### Gate 保护
1. ✅ Gate A: 契约验证
2. ✅ Gate B: E2E 验证
3. ✅ Gate C: 完整性验证

### 完整性规则
1. ✅ `all_passed=true` 时不得有任何 `check.passed=false`
2. ✅ `SUMMARY.md` 是必需产物
3. ✅ `receipt.json` 必须与 `gate_report.json` 同步
4. ✅ `task_state.status=completed` 时 ledger 必须有 `task_completed` 事件

---

## Breaking Changes 定义

以下改动被视为 **Breaking Change**，必须显式声明并重新验证：

### 破坏性改动
1. 修改 Gate 规则导致已通过任务失败
2. 删除或移动 `pilot_docs_index_v2` 任务目录
3. 修改 execution receipt schema 使已生成 receipt 无效
4. 修改 step packet schema 使已保存 packet 无效
5. 移除 SUMMARY.md 作为必需产物
6. 降低 Gate 严格度
7. 破坏中断恢复能力
8. 破坏"已成功步骤不重跑"保证

### 兼容改动
1. 新增 step_type
2. 新增 optional 字段
3. 新增测试
4. 新增文档
5. 新增回归检查
6. 性能优化不改变行为

---

## 回归保护

### 自动检查
- 检查脚本: `tools/check_v2_baseline.py`
- 回归测试: `tests/test_v2_baseline_guard.py`

### 检查项
1. SUMMARY.md 存在
2. gate_report.json 存在
3. receipt.json 存在
4. 三者一致
5. 无 Gate 矛盾
6. pilot 产出存在

---

## 引用文档

- [Gate Rules](GATE_RULES.md) - Gate 硬约束定义
- [Execution Design](CHECKPOINTED_STEP_LOOP_V2_EXECUTION.md) - 执行层设计
- [Long Task Loop v1](LONG_TASK_LOOP_V1.md) - v1 设计文档

---

## 版本历史

| 版本 | 日期 | 状态 |
|------|------|------|
| v2.0.0 | 2026-03-15 | FROZEN - Accepted Baseline |

---

## 后续路线

冻结后允许的改动：
- 新增测试和回归检查
- 新增 optional 功能
- 文档完善
- 性能优化

冻结后禁止的改动：
- 破坏现有已验证能力
- 降低 Gate 严格度
- 移除必需产物

进入 v3-A 前置条件：
- ✅ v2 baseline frozen
- ⏳ 回归保护就绪
- ⏳ 所有回归测试通过
