# OpenViking Runbook

## 服务管理

### 启动服务
```bash
openviking serve --config ~/.openviking/ov.conf &
```

### 停止服务
```bash
pkill -f openviking
```

### 检查状态
```bash
curl http://localhost:8000/health
pgrep -f openviking
```

---

## 常用操作

### 检索
```bash
openviking find "<query>" -u "viking://resources/user/" --limit 5
```

### 添加资源
```bash
openviking add-resource <file> --to "viking://resources/user/<namespace>/"
```

### 归档 session
```bash
~/.openclaw/workspace/tools/session-archive
```

---

## 故障排查

### 服务无法启动
```
Error: AGFS port 1833 is already in use
```
**解决**: 服务已在运行，无需重复启动。

### 检索无结果
**检查**:
1. 服务是否运行: `curl http://localhost:8000/health`
2. Ollama 是否运行: `curl http://192.168.79.1:11434/api/tags`
3. 是否有数据: 检查 `~/.openclaw/workspace/.openviking-data-local-ollama/`

### 归档失败
**检查**:
1. 日志: `journalctl --user -u openviking --since "10 min ago"`
2. 文件大小: 大文件需要先 distill

---

## 日志路径

```bash
# 服务日志
journalctl --user -u openviking --since "1 hour ago"

# 归档日志
cat ~/.openclaw/workspace/artifacts/openviking/archive/*/metrics.json
```

---

## 回滚

```bash
# 停止服务
pkill -f openviking

# 恢复原始归档流程
cp ~/.openclaw/workspace/tools/session-archive.original ~/.openclaw/workspace/tools/session-archive

# 删除 hook
rm -rf ~/.openclaw/hooks/compaction-archive
```

