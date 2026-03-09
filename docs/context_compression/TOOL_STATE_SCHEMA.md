# Tool State Schema

**Version**: 1.0  
**Created**: 2026-03-09

---

## 必须保留的 Tool State

| 字段 | 说明 | 优先级 |
|------|------|--------|
| tool_name | 工具名称 | 必需 |
| status | success/failed/called | 必需 |
| timestamp | 执行时间 | 必需 |
| target | 操作对象（文件/命令等）| 高 |
| result_summary | 结果摘要 | 高 |
| artifact_path | 生成的产物路径 | 中 |
| error_message | 失败原因（如果失败）| 中 |
| next_step | 下一步依赖 | 中 |

---

## 高优先恢复对象

1. **artifact 生成工具**
   - write, edit, exec（文件操作）
   - 记录产物路径

2. **Gate 相关工具**
   - verify-and-close
   - done-guard
   - 记录 Gate 通过状态

3. **验证类工具**
   - test runners
   - linters
   - 记录结果状态

---

## Tool State Anchor 评分

| 条件 | 加分 |
|------|------|
| 状态为 called（进行中）| +0.2 |
| 状态为 error | +0.2 |
| 生成了 artifact | +0.1 |
| 与 Gate 相关 | +0.1 |

---

## 实现状态

✅ `capsule-builder-v2.py` 已实现：
- 从 `role=tool` 事件提取工具状态
- 评分机制
- 去重逻辑

---
