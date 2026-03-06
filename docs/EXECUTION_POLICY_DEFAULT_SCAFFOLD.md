# Execution Policy v2.1 作为默认脚手架

**状态**: 已实施 (2026-03-06)
**版本**: v2.1 Trust Anchor

---

## 概述

从 2026-03-06 起，`install-execution-policy` 升级为新项目的**默认脚手架**。

这意味着：
- 新项目自动获得 Trust Anchor 链
- 所有子代理任务默认经过签名验证
- 状态机强制执行，防止跳过门禁

---

## 安装

```bash
# 在新项目目录下
cd /path/to/new-project
~/.openclaw/workspace/tools/install-execution-policy .

# 或指定目标目录
~/.openclaw/workspace/tools/install-execution-policy /path/to/project
```

---

## 安装内容

### 工具链

```
tools/
├── receipt-signer       # HMAC 签名/验证
├── gate-a-signer        # Gate A 独立签发
├── gate-b-signer        # Gate B 独立签发
├── gate-c-signer        # Gate C 独立签发
├── final-aggregator     # 收据聚合
├── state-authority      # 状态机裁决
├── verify-and-close-v2  # Trust Anchor 集成
├── safe-message         # 安全输出
├── verify-and-close → verify-and-close-v2  # 兼容软链接
└── done-guard → verify-and-close-v2        # 兼容软链接
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
└── doctor_report.v1.schema.json
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

## 工作流

### 任务完成流程

```
┌─────────────────┐
│  任务完成       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ verify-and-close│
│ (Trust Anchor)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Gate A  │ ← Contract validation
    │ Gate B  │ ← E2E testing
    │ Gate C  │ ← Preflight check
    └────┬────┘
         │
         ▼
┌─────────────────┐
│ final-aggregator│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ state-authority │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  safe-message   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   [用户消息]    │
└─────────────────┘
```

### 子代理流程

```bash
# 推荐：使用 spawn-with-callback 自动处理
~/.openclaw/workspace/tools/spawn-with-callback "任务描述" -m <model>

# 安装后自动获得 Trust Anchor 保护
```

---

## 模式

### Shadow Mode (默认)

- 记录所有违规
- 不阻止消息发送
- 用于观察期 (3-7 天)

### Enforce Mode

- 阻止无效签名的消息
- 阻止状态机绕过
- 用于生产环境

**切换到 Enforce Mode**:
```bash
export EXECUTION_POLICY_MODE=enforce
```

或在 `hook.json` 中设置 `"enforcementMode": "enforce"`

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

## 测试

```bash
# 正常测试
python3 tests/test_execution_policy.py

# 对抗测试
python3 tests/adversarial/test_execution_policy_adversarial.py
```

---

## 迁移指南

### 从 v1.0 升级

```bash
# 重新安装
~/.openclaw/workspace/tools/install-execution-policy . --version v2.1

# 或手动复制新工具
cp ~/.openclaw/workspace/tools/receipt-signer tools/
cp ~/.openclaw/workspace/tools/gate-a-signer tools/
# ... 等
```

### 兼容性

- `verify-and-close` 软链接到 `verify-and-close-v2`
- `done-guard` 软链接到 `verify-and-close-v2`
- 旧脚本无需修改

---

## 参考

- `docs/releases/TRUST_ANCHOR_v2.1_HANDOFF.md` - 架构详情
- `docs/releases/NATIVE_HOOK_INTEGRATION.md` - Hook 集成指南
- `docs/EXECUTION_POLICY.md` - 完整协议
