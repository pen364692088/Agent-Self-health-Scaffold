# Tool Delivery Gates Changelog

## [v2.0] - 2026-03-04

### Added
- **路径触发白名单/黑名单配置化** (`POLICIES/GATES_CONFIG.json`)
  - Whitelist: tools/, integrations/, handlers/, schemas/, skills/, hooks/
  - Blacklist: docs/, README, CHANGELOG, test_fixtures/
  - 路径优先于关键词检测

- **JSON Schema 固化** (`schemas/doctor_report.v1.schema.json`)
  - doctor.v1 schema 定义所有必需字段和类型
  - done-guard v2.1 支持 schema 验证

- **transport=http 最小 E2E 用例**
  - tool_doctor v2.0 支持 --transport http/local
  - http 模式真实调用工具端点
  - report 中明确 mode 和 transport

- **CI skip allowlist**
  - 允许跳过的分支: staging, dev
  - 允许跳过的 labels: skip-gates, hotfix
  - 跳过必须生成 gates_skip_justification.md artifact

- **GATES_DISABLE 审计日志**
  - 所有绕过记录到 reports/gates_audit.log
  - 要求提供 GATES_DISABLE_REASON

### Enhanced
- **subtask-orchestrate v2.2**
  - 路径触发强制 gates
  - 审计日志记录绕过

- **done-guard v2.1**
  - JSON schema 验证
  - 证据真实性校验（文件存在 + 字段齐全）

- **tool_doctor v2.0**
  - 两种 transport 模式
  - 详细 error_code + 可行动 message
  - CI 模式 mock sample call

- **CI workflow v2.0**
  - 禁止静默 skip
  - 上传 doctor_report artifacts
  - Skip justification artifact

### Files Changed
- `POLICIES/TOOL_DELIVERY.md` - 全局协议文件
- `POLICIES/GATES_CONFIG.json` - 配置文件 (新增)
- `schemas/doctor_report.v1.schema.json` - Schema 定义 (新增)
- `tools/subtask-orchestrate` - v2.2
- `tools/done-guard` - v2.1
- `tools/tool_doctor` - v2.0
- `.github/workflows/tool-gates.yml` - v2.0

### Verification
```bash
# 测试工具任务检测
subtask-orchestrate detect "build API tool" --json

# 测试路径触发
subtask-orchestrate detect "random" --json
# 改动 tools/ 自动触发 is_tool_task: true

# 测试 schema 验证
done-guard --validate-doctor reports/tool_doctor/doctor_report.json

# 测试 tool_doctor
tool_doctor <tool> --transport http --ci
```

---

## [v1.0] - 2026-03-04 (Initial)

### Added
- POLICIES/TOOL_DELIVERY.md - 三个 Gate 定义
- Prompt 注入逻辑 - 工具任务自动注入协议
- done-guard - Evidence 检查
- tool_doctor - Preflight 检查工具
- CI workflow - GitHub Actions gate

