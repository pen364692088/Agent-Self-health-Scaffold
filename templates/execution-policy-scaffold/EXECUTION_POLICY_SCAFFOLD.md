# Execution Policy Scaffold

新项目默认接入 Execution Policy 的模板。

## 快速接入

```bash
# 1. 复制工具
cp -r ~/.openclaw/workspace/tools/verify-and-close ./tools/
cp -r ~/.openclaw/workspace/tools/done-guard ./tools/
cp -r ~/.openclaw/workspace/tools/finalize-response ./tools/
cp -r ~/.openclaw/workspace/tools/output-interceptor ./tools/
cp -r ~/.openclaw/workspace/tools/receipt-validator ./tools/
cp -r ~/.openclaw/workspace/tools/safe-message ./tools/

# 2. 复制 schema
mkdir -p schemas
cp ~/.openclaw/workspace/schemas/task_receipt.v1.schema.json ./schemas/

# 3. 复制 CI workflow
mkdir -p .github/workflows
cp ~/.openclaw/workspace/.github/workflows/execution-policy-gate.yml .github/workflows/

# 4. 复制测试
mkdir -p tests
cp ~/.openclaw/workspace/tests/test_execution_policy.py ./tests/

# 5. 创建必要目录
mkdir -p artifacts/receipts reports
```

## 默认规则 (添加到 AGENTS.md 或 SOUL.md)

```markdown
## Task Completion Protocol (强制)

**所有工程类任务的完成必须通过：**

1. `verify-and-close --task-id <id>` - 生成 receipts
2. `finalize-response --task-id <id> --summary "..."` - 检查
3. `safe-message --task-id <id> --message "..."` - 安全发送

**禁止：**
- ❌ 直接输出"已完成"类表述
- ❌ 跳过 verify-and-close
- ❌ 直接调用 message tool

**测试：**
- `pytest tests/test_execution_policy.py` - 13 个测试
```

## CI Required Check

```yaml
# .github/workflows/execution-policy-gate.yml
name: Execution Policy Gate

on:
  pull_request:
    paths:
      - 'tools/**'
      - 'handlers/**'
      - 'schemas/**'

jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 tests/test_execution_policy.py
```

## 退化监控

```bash
# 每小时检查
0 * * * * ~/.openclaw/workspace/tools/execution-degradation-monitor --check

# 每日报告
0 9 * * * ~/.openclaw/workspace/tools/execution-degradation-monitor --report
```

## 对抗测试

```bash
# 运行对抗测试
python3 tests/adversarial/test_execution_policy_adversarial.py
```

## 文件结构

```
.
├── tools/
│   ├── verify-and-close
│   ├── done-guard
│   ├── finalize-response
│   ├── output-interceptor
│   ├── receipt-validator
│   └── safe-message
├── schemas/
│   └── task_receipt.v1.schema.json
├── artifacts/
│   └── receipts/
├── reports/
│   ├── interceptor_log.jsonl
│   ├── finalize_log.jsonl
│   └── execution_metrics.jsonl
├── tests/
│   ├── test_execution_policy.py
│   └── adversarial/
│       └── test_execution_policy_adversarial.py
└── .github/
    └── workflows/
        └── execution-policy-gate.yml
```
