# USER.md - About Your Human

_Learn about the person you're helping. Update this as you go._

- **Name:**
- **What to call them:**
- **Pronouns:** _(optional)_
- **Timezone:**
- **Notes:**

## Context

- 用户提供了技能参考仓库：`https://github.com/VoltAgent/awesome-openclaw-skills`
- 偏好：有新任务时，优先从该库检索可用 skill，再给出选项、风险提示与推荐安装项。
- 重要偏好（更新）：默认视为用户自有项目仓库；后续 GitHub 提交/推送（含 push 到远端）默认自动执行。

---

The more you know, the better you can help. But remember — you're learning about a person, not building a dossier. Respect the difference.

---

## Tool Delivery Gates 强制执行

**所有工具/集成/处理器相关项目必须严格遵守 Tool Delivery Gates v2.0 协议。**

### 强制规则

1. **三个 Gate 必须通过**
   - Gate A: Contract Validation (schema + drift + error format)
   - Gate B: E2E Testing (happy path + bad args)
   - Gate C: Preflight Check (tool_doctor + doctor_report.json)

2. **Evidence 必须**
   - 最终输出必须包含 EVIDENCE_GATE_A/B/C 三个区块
   - Evidence 必须真实（文件存在 + 字段齐全）

3. **路径触发自动生效**
   - 改动 tools/**, integrations/**, handlers/**, schemas/** 自动强制 gates
   - 不需要用户明确说"这是工具任务"

4. **GATES_DISABLE 仅限紧急**
   - 必须提供 GATES_DISABLE_REASON
   - 会被审计记录（config_hash + schema_version + tool_versions）

5. **skip-gates label**
   - 只有 Owners/Maintainers 可以添加
   - 仅限 staging/dev 分支或 hotfix PR

### 文档位置

- 协议: `POLICIES/TOOL_DELIVERY.md`
- 配置: `POLICIES/GATES_CONFIG.json`
- 运行手册: `POLICIES/OPERATIONS.md`
- Schema: `schemas/doctor_report.v1.schema.json`

---
Added: 2026-03-04 03:14 CST
- 新偏好（2026-03-04）：workspace 相关归档/会话总结，默认采用“顶层备份仓库提交”流程（`/home/moonlight/.openclaw`），以 `session-archives/*.md` 摘要迁移方式提交并推送；不直接依赖 workspace 仓库 push。
