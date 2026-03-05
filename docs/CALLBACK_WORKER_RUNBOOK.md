# Callback Worker 运行手册

## 状态检查

```bash
# 服务状态
systemctl --user status callback-worker

# 健康检查
callback-worker-doctor

# 指标
callback-handler-auto --metrics

# 队列
event-queue list
```

---

## 紧急操作

### 停止自动推进

```bash
# 方式 1: 文件开关（推荐）
touch ~/.openclaw/workspace/STOP_AUTO_ADVANCE

# 方式 2: 环境变量
export AUTO_ADVANCE_ENABLED=0

# 方式 3: 停止服务
systemctl --user stop callback-worker

# 方式 4: CLI
callback-handler-auto --kill-switch
```

### 恢复运行

```bash
# 删除停止文件
rm ~/.openclaw/workspace/STOP_AUTO_ADVANCE

# 或 CLI
callback-handler-auto --unkill

# 重启服务
systemctl --user start callback-worker
```

---

## 日志查看

```bash
# systemd 日志（实时）
journalctl --user -u callback-worker -f

# 最近 10 分钟日志
journalctl --user -u callback-worker --since "10 min ago"

# 文件日志
tail -f ~/.openclaw/workspace/logs/callback-worker.log
tail -f ~/.openclaw/workspace/logs/callback-auto-*.log
```

---

## 故障排查

### 问题 1: 推进延迟过高

**症状**: E2E 延迟 > 5s

**检查**:
```bash
callback-handler-auto --metrics | jq '.advances | map(.latency_ms) | add / length'
```

**可能原因**:
- 队列积压
- spawn backend 慢
- 并发上限卡住

**解决**:
- 检查队列: `event-queue list`
- 检查并发: `callback-handler-auto --health | jq '.global_inflight'`

### 问题 2: spawn 成功率下降

**症状**: 成功率 < 95%

**检查**:
```bash
callback-handler-auto --metrics | jq '[.advances[] | select(.success == false)] | length'
```

**可能原因**:
- API 限流
- 模型不可用
- 权限问题

**解决**:
- 检查日志中的错误
- 检查 API 配置

### 问题 3: 死循环护栏触发

**症状**: 推进被拒绝，日志显示 `rate_limit_exceeded`

**检查**:
```bash
callback-handler-auto --health | jq '.config'
```

**可能原因**:
- workflow 设计错误
- 异常循环触发

**解决**:
- 检查 workflow 状态
- 修复 workflow 设计
- 必要时调整阈值

---

## 升级流程

```bash
# 1. 停止服务
systemctl --user stop callback-worker

# 2. 备份状态
cp ~/.openclaw/workspace/WORKFLOW_STATE.json ~/.openclaw/workspace/WORKFLOW_STATE.json.backup

# 3. 升级代码
# ... (git pull 或其他方式)

# 4. 健康检查
callback-worker-doctor

# 5. 启动服务
systemctl --user start callback-worker

# 6. 观察指标
callback-handler-auto --metrics
journalctl --user -u callback-worker -f
```

---

## 告警阈值

| 指标 | 正常 | 告警 | 紧急 |
|------|------|------|------|
| E2E 延迟 (p95) | < 2s | > 5s 持续 5 分钟 | > 10s |
| spawn 成功率 | > 99% | < 95% | < 90% |
| rollback 次数 | ~0 | > 3/小时 | > 10/小时 |
| queue depth | < 10 | 持续增长 | > 100 |
| 死循环触发 | 0 | 任何触发 | - |

---

## 联系方式

- 文档: `/tmp/CALLBACK_GO_LIVE_CHECKLIST.md`
- 护栏验证: `verify-callback-guards`
- Path A 测试: `test-callback-acceptance`
- Path B 测试: `test-path-b-acceptance`

