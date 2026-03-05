# Workflow Integration Guide

**2 分钟接入自动推进系统。**

---

## 快速开始

### 1. 编写 workflow_spec.json

```json
{
  "workflow_id": "my_workflow",
  "workflow_type": "serial",
  "steps": [
    {
      "id": "step_1",
      "payload": {
        "model": "baiduqianfancodingplan/qianfan-code-latest",
        "task": "任务描述",
        "timeout": 600
      }
    },
    {
      "id": "step_2",
      "payload": {
        "model": "baiduqianfancodingplan/qianfan-code-latest",
        "task": "下一个任务",
        "timeout": 600
      }
    }
  ]
}
```

### 2. 初始化工作流

```bash
workflow-init my_workflow_spec.json
```

### 3. 启动 callback-worker

```bash
systemctl --user start callback-worker
```

### 4. 触发推进

当步骤完成时，入队事件：

```bash
event-queue enqueue <run_id> --workflow-id my_workflow
```

---

## 详细步骤

### Step 1: 定义工作流

创建 `workflow_spec.json`:

```json
{
  "workflow_id": "feature_deployment",
  "workflow_type": "serial",
  "steps": [
    {
      "id": "code_review",
      "payload": {
        "model": "baiduqianfancodingplan/qianfan-code-latest",
        "task": "Review code changes",
        "cwd": "/path/to/repo",
        "timeout": 300
      }
    },
    {
      "id": "run_tests",
      "payload": {
        "model": "baiduqianfancodingplan/qianfan-code-latest",
        "task": "Run test suite",
        "cwd": "/path/to/repo",
        "timeout": 600
      }
    },
    {
      "id": "deploy",
      "payload": {
        "model": "baiduqianfancodingplan/qianfan-code-latest",
        "task": "Deploy to production",
        "cwd": "/path/to/repo",
        "timeout": 300
      }
    }
  ],
  "limits": {
    "max_advances_per_hour": 20,
    "max_advances_per_workflow": 10
  },
  "hooks": {
    "on_done": {
      "notify": {
        "channel": "telegram",
        "message": "✅ Deployment complete"
      }
    }
  }
}
```

### Step 2: 校验规范

```bash
workflow-init my_spec.json --validate-only
```

### Step 3: 初始化状态

```bash
workflow-init my_spec.json --output /path/to/state/dir
```

### Step 4: 启动服务

```bash
# 使用 systemd
systemctl --user start callback-worker

# 或手动运行
callback-worker --listen
```

### Step 5: 触发推进

当子代理完成时：

```bash
# 在子代理完成处添加
event-queue enqueue <run_id> --workflow-id feature_deployment
```

---

## 监控与调试

### 查看状态

```bash
# 工作流状态
workflow-validate

# 指标
callback-handler-auto --metrics

# 队列
event-queue list

# 健康检查
callback-worker-doctor
```

### 查看日志

```bash
# systemd 日志
journalctl --user -u callback-worker -f

# 文件日志
tail -f ~/.openclaw/workspace/logs/callback-worker.log
```

### 紧急停止

```bash
touch ~/.openclaw/workspace/STOP_AUTO_ADVANCE
```

---

## 常见问题

### Q: 如何调试工作流？

```bash
# 1. 查看状态
workflow-validate

# 2. 查看日志
journalctl --user -u callback-worker --since "10 min ago"

# 3. 手动触发（测试）
event-queue enqueue test_run --workflow-id test
```

### Q: 如何重试失败的步骤？

失败会自动重试（最多 3 次）。如果需要手动重试：

```bash
# 清除错误状态
jq '.steps[0].status = "done" | .steps[0].advance_processed = false' WORKFLOW_STATE.json > tmp.json && mv tmp.json WORKFLOW_STATE.json

# 触发推进
event-queue enqueue <run_id>
```

### Q: 如何修改工作流？

```bash
# 1. 停止服务
systemctl --user stop callback-worker

# 2. 修改 WORKFLOW_STATE.json

# 3. 重启服务
systemctl --user start callback-worker
```

---

## 最佳实践

1. **设置合理的 limits**: 根据工作流复杂度调整
2. **添加 hooks**: 完成时通知
3. **监控指标**: 定期检查成功率和延迟
4. **保留日志**: 便于复盘

---

## 参考资料

- [WORKFLOW_AUTO_ADVANCE.md](../POLICIES/WORKFLOW_AUTO_ADVANCE.md) - 规范主文档
- [WORKFLOW_SPEC.schema.json](../POLICIES/WORKFLOW_SPEC.schema.json) - Spec Schema
- [WORKFLOW_STATE.schema.json](../POLICIES/WORKFLOW_STATE.schema.json) - State Schema

