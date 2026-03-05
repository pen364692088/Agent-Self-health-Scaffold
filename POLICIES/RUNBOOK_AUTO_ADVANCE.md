# Runbook: Auto-Advance System

**运维手册 - 自动推进系统**

---

## 启停命令

### 启动服务

```bash
systemctl --user start callback-worker
systemctl --user status callback-worker
```

### 停止服务

```bash
systemctl --user stop callback-worker
```

### 紧急停止（保持服务运行，但停止推进）

```bash
# 方式 1: 文件开关
touch ~/.openclaw/workspace/STOP_AUTO_ADVANCE

# 方式 2: 环境变量
export AUTO_ADVANCE_ENABLED=0

# 方式 3: CLI
callback-handler-auto --kill-switch
```

### 恢复运行

```bash
rm ~/.openclaw/workspace/STOP_AUTO_ADVANCE
callback-handler-auto --unkill
systemctl --user start callback-worker
```

---

## 指标查看与阈值建议

### 查看指标

```bash
callback-handler-auto --metrics
callback-daily-summary
```

### 阈值建议

| 指标 | 正常 | 告警 | 紧急 |
|------|------|------|------|
| E2E 延迟 (p95) | < 500ms | > 1s 持续 5 分钟 | > 5s |
| Spawn 成功率 | > 99% | < 95% | < 90% |
| Rollback 次数 | ~0 | > 3/小时 | > 10/小时 |
| Queue depth | < 10 | 持续增长 | > 100 |
| 死循环触发 | 0 | 任何触发 | - |

---

## 常见故障

### 1. State 损坏

**症状**: JSON 解析错误，状态不一致

**诊断**:
```bash
jq '.' ~/.openclaw/workspace/WORKFLOW_STATE.json
workflow-validate
```

**修复**:
```bash
# 从备份恢复
cp ~/.openclaw/workspace/WORKFLOW_STATE.json.backup ~/.openclaw/workspace/WORKFLOW_STATE.json

# 或手动修复 JSON
```

### 2. Inflight 卡住

**症状**: 推进无法进行，日志显示 inflight 状态

**诊断**:
```bash
workflow-validate | grep inflight
```

**修复**:
```bash
# 清除 inflight（谨慎操作）
jq '.steps[].advance_inflight = null' WORKFLOW_STATE.json > tmp.json && mv tmp.json WORKFLOW_STATE.json
```

### 3. Spawn 失败

**症状**: 推进失败，last_error 有值

**诊断**:
```bash
callback-handler-auto --metrics | jq '.advances[-5:]'
journalctl --user -u callback-worker --since "10 min ago" | grep -i error
```

**修复**:
- 检查 spawn backend（API/CLI）
- 检查模型可用性
- 检查权限

### 4. 队列堆积

**症状**: queue depth 持续增长

**诊断**:
```bash
event-queue list
```

**修复**:
```bash
# 检查 worker 是否运行
systemctl --user status callback-worker

# 手动消费（测试）
event-queue consume

# 清理队列（谨慎）
rm ~/.openclaw/workspace/events/*.json
```

### 5. 死循环触发

**症状**: 推进被拒绝，rate_limit_exceeded

**诊断**:
```bash
callback-handler-auto --health
```

**修复**:
- 检查 workflow 设计
- 调整 limits
- 必要时启用 kill-switch

---

## 应急刹车流程

### 1. 先停

```bash
touch ~/.openclaw/workspace/STOP_AUTO_ADVANCE
systemctl --user stop callback-worker
```

### 2. 取证

```bash
# 收集日志
journalctl --user -u callback-worker --since "30 min ago" > /tmp/callback-worker.log

# 收集指标
callback-handler-auto --metrics > /tmp/metrics.json

# 收集状态
cp ~/.openclaw/workspace/WORKFLOW_STATE.json /tmp/
cp -r ~/.openclaw/workspace/events/ /tmp/
```

### 3. 恢复

```bash
# 修复问题后
rm ~/.openclaw/workspace/STOP_AUTO_ADVANCE
systemctl --user start callback-worker

# 观察指标
callback-handler-auto --metrics
```

---

## 升级回滚 SOP

### 升级流程

```bash
# 1. 停止服务
systemctl --user stop callback-worker

# 2. 备份状态
cp ~/.openclaw/workspace/WORKFLOW_STATE.json ~/.openclaw/workspace/WORKFLOW_STATE.json.backup

# 3. 升级代码
git pull  # 或其他方式

# 4. 健康检查
callback-worker-doctor

# 5. 启动服务
systemctl --user start callback-worker

# 6. 观察指标
callback-handler-auto --metrics
journalctl --user -u callback-worker -f
```

### 回滚流程

```bash
# 1. 停止服务
systemctl --user stop callback-worker

# 2. 回滚代码
git checkout <previous-commit>

# 3. 恢复状态（如果需要）
cp ~/.openclaw/workspace/WORKFLOW_STATE.json.backup ~/.openclaw/workspace/WORKFLOW_STATE.json

# 4. 启动服务
systemctl --user start callback-worker
```

---

## 兜底扫描归因

### fallback_reason 枚举

| 值 | 说明 | 正常频率 |
|------|------|---------|
| `event_missing` | 事件未入队 | < 10% |
| `state_lag` | 事件先到但 state 未落盘 | < 5% |
| `backoff_expired` | 退避到期 | 取决于重试率 |
| `startup_sweep` | 启动扫描 | 仅启动时 |
| `opportunistic` | 机会性扫描 | 低频 |
| `manual_once` | 手动触发 | 按需 |

### 日志格式

```
[fallback] reason=event_missing step=step_a run_id=xxx workflow_id=yyy
```

### 排障建议

- `event_missing` 高 → 检查入队挂钩
- `state_lag` 高 → 检查 state 落盘延迟
- `backoff_expired` 高 → 检查失败原因

---

## 联系方式

- 文档: `~/.openclaw/workspace/docs/`
- 工具: `~/.openclaw/workspace/tools/`
- Schema: `~/.openclaw/workspace/POLICIES/`

