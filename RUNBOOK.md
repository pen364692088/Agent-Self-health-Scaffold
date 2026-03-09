# RUNBOOK.md - 系统运维手册

**Version**: 1.0 | **Last Updated**: 2026-03-09

---

## 系统状态总览

| 组件 | 状态 | 备注 |
|------|------|------|
| Native Compaction | ✅ RESTORED | 已验证通过 |
| OpenViking | ✅ ENABLED | 已验证通过 |
| OpenClaw Gateway | ✅ Running | localhost:6060 |

---

## OpenViking

### 服务管理

```bash
# 启动服务
openviking serve --config ~/.openviking/ov.conf &

# 停止服务
pkill -f openviking

# 检查状态
curl http://localhost:8000/health
pgrep -f openviking
```

### 常用操作

```bash
# 检索
openviking find "<query>" -u "viking://resources/user/" --limit 5

# 添加资源
openviking add-resource <file> --to "viking://resources/user/<namespace>/"

# 归档 session（已集成 distill + OpenViking）
~/.openclaw/workspace/tools/session-archive
```

### 故障排查

| 问题 | 检查 | 解决 |
|------|------|------|
| 服务无法启动 | `curl localhost:8000/health` | 可能已运行，无需重复启动 |
| 检索无结果 | 检查 Ollama: `curl 192.168.79.1:11434/api/tags` | 确保 embedding 模型可用 |
| 归档失败 | `journalctl --user -u openviking` | 大文件需先 distill |

### 回滚

```bash
# 停止服务
pkill -f openviking

# 恢复原始归档流程
cp ~/.openclaw/workspace/tools/session-archive.original ~/.openclaw/workspace/tools/session-archive
```

---

## Native Compaction

### 正确入口

| 入口 | 用途 |
|------|------|
| `/compact` 命令 | 手动触发压缩 |
| 自动触发 | context > window - 16k tokens |

### 禁止误用

| 错误入口 | 原因 |
|---------|------|
| `sessions.compact` RPC | 仅是行数截断工具（阈值 400 行） |

### 验证样本要求

- ✅ 必须包含 user/assistant/toolResult 消息
- ❌ 事件日志型 session 无效

---

## Session 归档

### 手动归档

```bash
~/.openclaw/workspace/tools/session-archive
```

### 自动归档

已通过 `after_compaction` hook 集成，compaction 成功后自动归档。

### 归档流程

```
原始文件 → distill-content (LLM提炼) → OpenViking入库 → git提交
```

---

## 日志路径

```bash
# OpenViking 日志
journalctl --user -u openviking --since "1 hour ago"

# OpenClaw Gateway 日志
journalctl --user -u openclaw --since "1 hour ago"

# 归档日志
cat ~/.openclaw/workspace/artifacts/openviking/archive/*/metrics.json

# Subagent 回执
ls ~/.openclaw/workspace/reports/subtasks/
```

---

## 快速诊断

```bash
# 系统状态
openclaw status

# Gateway 状态
openclaw gateway status

# Session 列表
openclaw sessions --all-agents --json | jq '.sessions[].key'

# OpenViking 健康
curl -s http://localhost:8000/health

# Ollama 模型
curl -s http://192.168.79.1:11434/api/tags | jq '.models[].name'
```

---

## 相关文档

- `POLICIES/COMPACTION_VERIFICATION_RUNBOOK.md` - Compaction 验证规则
- `artifacts/openviking-enablement/OPENVIKING_RUNBOOK.md` - OpenViking 详细 runbook
- `artifacts/real_session_compaction_test/FINAL_VERDICT.md` - Compaction 恢复报告
- `artifacts/openviking-enablement/FINAL_OPENVIKING_ENABLEMENT_VERDICT.md` - OpenViking 启用报告

---

**Version History**:
- v1.0 (2026-03-09): 初始版本，整合 OpenViking + Compaction
