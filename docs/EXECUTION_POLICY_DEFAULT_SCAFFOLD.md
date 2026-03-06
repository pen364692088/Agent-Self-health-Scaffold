# Execution Policy v2.2 默认脚手架

**状态**: 已实施 (2026-03-06)
**版本**: v2.2 - Shadow Mode First

---

## 核心设计原则

1. **Shadow Mode First** - 新项目默认观察模式，不硬拦
2. **Explicit Opt-out** - 保留显式退出路径
3. **Two-Phase Activation** - 满足条件后再切 Enforced
4. **Self-Check** - 安装后自动验证

---

## 安装

```bash
# 默认 Shadow mode (推荐)
~/.openclaw/workspace/tools/install-execution-policy /path/to/project

# 强制 Enforce mode (不推荐新项目)
~/.openclaw/workspace/tools/install-execution-policy /path/to/project --enforce

# 显式退出
~/.openclaw/workspace/tools/install-execution-policy /path/to/project --no-execution-policy
```

---

## 模式对比

| 模式 | 行为 | 适用场景 |
|------|------|---------|
| **Shadow** (默认) | 记录违规，不阻止 | 新项目、观察期 |
| **Enforce** | 阻止无效消息 | 经过验证的生产环境 |

---

## 安装内容

### 工具链 (15 个)

```
tools/
├── receipt-signer           # HMAC 签名/验证
├── gate-a-signer            # Gate A 独立签发
├── gate-b-signer            # Gate B 独立签发
├── gate-c-signer            # Gate C 独立签发
├── final-aggregator         # 收据聚合
├── state-authority          # 状态机裁决
├── verify-and-close-v2      # Trust Anchor 集成
├── safe-message             # 安全输出
├── finalize-response        # 响应处理
├── done-guard               # 完成守卫
├── output-interceptor       # 输出拦截
├── receipt-validator        # 收据验证
├── execution-metrics        # 执行指标
├── execution-degradation-monitor  # 退化监控
└── completion-bypass-audit  # 旁路审计
```

### 原生 Hook

```
hooks/execution-policy-enforcer/
├── hook.json     # 配置 (shadow mode)
└── handler.js    # 预发送中间件
```

### Schema

```
schemas/
├── task_receipt.v1.schema.json
├── doctor_report.v1.schema.json
└── subagent_receipt.v1.schema.json
```

### 测试

```
tests/
├── test_execution_policy.py
└── adversarial/
    └── test_execution_policy_adversarial.py
```

### CI

```
.github/workflows/
└── execution-policy-gate.yml
```

---

## 显式退出

### 命令行

```bash
install-execution-policy /path/to/project --no-execution-policy
```

### 环境变量

```bash
export EXECUTION_POLICY_DISABLED=1
```

---

## 两阶段启用策略

### Phase 1: Shadow (新项目默认)

```
安装 → 观察期 → 收集违规日志 → 验证指标
```

**观察期目标**:
- 收集 shadow_log 数据
- 识别误报/漏报
- 验证测试覆盖

### Phase 2: Enforce (验证后切换)

**切换条件**:
- [ ] 正常测试通过
- [ ] 对抗测试通过
- [ ] Happy path 验证
- [ ] 旁路审计无高风险
- [ ] 指标稳定 3-7 天

**切换方法**:

```bash
# 方法 1: 环境变量
export EXECUTION_POLICY_MODE=enforce

# 方法 2: 修改 hook.json
# "enforcementMode": "enforce"

# 方法 3: 重新安装
install-execution-policy /path/to/project --enforce
```

---

## 安装后自检

安装脚本自动运行 6 项检查:

| 检查项 | 说明 |
|--------|------|
| Hook registered | hook.json 存在 |
| receipt-signer | 工具可执行 |
| state-authority | 工具可执行 |
| Schema exists | schema 文件存在 |
| CI workflow | workflow 文件存在 |
| Tools directory | 目录结构完整 |

跳过自检: `--skip-checks`

---

## 启用 Hook

编辑 `~/.openclaw/openclaw.json`:

```json
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "emotiond-enforcer": { "enabled": true },
        "execution-policy-enforcer": { "enabled": true }
      }
    }
  }
}
```

---

## Shadow Log

Shadow 模式下，违规记录到:

```
artifacts/shadow_log/execution_policy_audit.jsonl
```

每条记录包含:
- `timestamp` - 时间戳
- `target_id` - 目标 ID
- `policy_check` - 策略检查结果
- `mode` - 当前模式
- `action_taken` - 采取的动作 (shadow_logged)

---

## 示例输出

```
╔════════════════════════════════════════════════════════════╗
║  Execution Policy v2.1 - Default Scaffold              ║
║  Mode: shadow                                              ║
╚════════════════════════════════════════════════════════════╝

Target: /path/to/project

▸ Creating directory structure...
  ✓ directories created
▸ Installing Trust Anchor tools...
  ✓ receipt-signer
  ✓ gate-a-signer
  ...
  Installed: 15, Skipped: 0
▸ Running installation checks...
  ✓ Hook registered
  ✓ receipt-signer
  ✓ state-authority
  ✓ Schema exists
  ✓ CI workflow
  ✓ Tools directory

  Checks: 6 passed, 0 failed

╔════════════════════════════════════════════════════════════╗
║  ✅ Execution Policy v2.1 Installed                     ║
╚════════════════════════════════════════════════════════════╝

Mode: shadow

📋 Shadow Mode Active
   - Violations will be LOGGED, not blocked
   - Review artifacts/shadow_log/ for violations
   - Switch to enforce mode after validation
```

---

## 参考

- `docs/releases/TRUST_ANCHOR_v2.1_HANDOFF.md` - 架构详情
- `docs/releases/NATIVE_HOOK_INTEGRATION.md` - Hook 集成指南
