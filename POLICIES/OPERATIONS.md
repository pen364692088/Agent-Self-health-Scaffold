# Tool Delivery Gates v2.0 - Operations Manual

**Version**: v2.0 | **Last Updated**: 2026-03-04

---

## 1. GATES_DISABLE 使用规则

### 何时使用
只有在以下紧急情况下才能使用 `GATES_DISABLE=1`：

1. **生产事故修复** - 需要立即部署 hotfix
2. **阻塞依赖** - 外部服务不可用导致无法完成 gate
3. **CI 基础设施故障** - GitHub Actions 或关键服务宕机

### 必须操作
```bash
# 设置 GATES_DISABLE
export GATES_DISABLE=1

# 必须提供原因（强制）
export GATES_DISABLE_REASON="生产事故 P0 修复：数据库连接池泄漏"

# 执行任务
subtask-orchestrate run "<task>" -m <model>
```

### 审计追踪
所有 GATES_DISABLE 使用都会记录到：
- `reports/gates_audit.log`
- 包含：timestamp, reason, user, task_id, config_hash, schema_version, tool_versions

---

## 2. skip-gates Label 审批规则

### 谁可以添加
只有 **Repository Owners** 和 **Maintainers** 可以添加 `skip-gates` 或 `hotfix` label。

### 审批流程
1. 创建 PR
2. 添加评论：`@maintainers please add skip-gates label with reason: <reason>`
3. Maintainer 审核并添加 label
4. CI workflow 自动验证 label 权限

### 权限检查
- GitHub Actions 会自动检查添加 label 的用户权限
- 非授权用户添加的 label 会被自动移除
- 所有 label 使用都会记录到 workflow summary

### 允许的分支
即使有 label，以下分支才允许跳过：
- `staging`
- `dev`
- 带有 `skip-gates` 或 `hotfix` label 的 PR

---

## 3. 常见失败修复指南

### 失败类型 A: 端口被占用 (EADDRINUSE)

**症状**:
```
error: Port 8080 already in use (EADDRINUSE)
```

**修复**:
```bash
# 方案 1: 使用 PORT=0 自动分配
PORT=0 tool_doctor <tool>

# 方案 2: 查找并杀掉占用进程
lsof -i :8080
kill <PID>

# 方案 3: 换端口
PORT=9000 tool_doctor <tool>
```

---

### 失败类型 B: Token/认证缺失

**症状**:
```
error: Missing required environment variable: API_TOKEN
```

**修复**:
```bash
# 检查配置
env | grep TOKEN

# 设置缺失的 token
export API_TOKEN="your-token-here"

# 或在 .env 文件中配置
echo "API_TOKEN=xxx" >> .env
```

---

### 失败类型 C: Schema 不匹配

**症状**:
```
Schema validation failed:
- Missing required field: health_ok
- Field 'status' value 'ok' not in enum: ['healthy', 'unhealthy']
```

**修复**:
```bash
# 检查 doctor_report.json 格式
cat reports/tool_doctor/doctor_report.json | jq .

# 验证 schema
done-guard --validate-doctor reports/tool_doctor/doctor_report.json

# 确保 report 包含所有必需字段：
# - tool, timestamp, mode, transport, status
# - checks (array), summary, chosen_port
# - health_ok (boolean), sample_call_ok (boolean)
```

---

### 失败类型 D: 路径触发误判

**症状**:
- 任务被错误识别为工具任务
- 或工具任务未被识别

**修复**:
```bash
# 检查配置
cat POLICIES/GATES_CONFIG.json | jq '.tool_detection.path_triggers'

# 白名单路径（强制触发）:
# tools/, integrations/, handlers/, schemas/, skills/, hooks/

# 黑名单路径（永不触发）:
# docs/, README, CHANGELOG, test_fixtures/

# 手动测试检测
subtask-orchestrate detect "<task>" --json

# 如果需要调整，编辑 POLICIES/GATES_CONFIG.json
```

---

### 失败类型 E: E2E 测试在 CI 无法运行

**症状**:
```
error: No E2E tests found and ALLOW_E2E_SKIP is not set
```

**修复**:
```bash
# 方案 1: 添加 E2E 测试文件
# 创建 test_*_e2e.py 或 *_e2e_test.py

# 方案 2: 临时允许跳过（不推荐）
# 在 GitHub repository variables 中设置:
# ALLOW_E2E_SKIP=1

# 方案 3: 使用 --ci 模式的 tool_doctor
tool_doctor <tool> --ci
```

---

## 4. 快速诊断命令

```bash
# 检查系统状态
subtask-orchestrate status

# 测试工具任务检测
subtask-orchestrate detect "<task>" --json

# 运行 tool_doctor
tool_doctor <tool> --ci --json

# 验证 doctor_report
done-guard --validate-doctor reports/tool_doctor/doctor_report.json

# 检查审计日志
tail -20 reports/gates_audit.log

# 检查配置
cat POLICIES/GATES_CONFIG.json | jq .
```

---

## 5. 联系方式

- **问题反馈**: 创建 GitHub Issue
- **紧急联系**: @moonlight
- **文档位置**: `POLICIES/TOOL_DELIVERY.md`

---

**Version History**:
- v2.0 (2026-03-04): 初始版本
