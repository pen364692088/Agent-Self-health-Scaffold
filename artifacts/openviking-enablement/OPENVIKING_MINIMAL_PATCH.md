# OpenViking Minimal Patch

## 改动点

### 1. 服务重启（已完成）
```bash
pkill -f openviking
openviking serve --config ~/.openviking/ov.conf &
```

### 2. 归档流程更新（已完成）
- 创建 `tools/distill-content` - LLM 提炼
- 创建 `tools/archive-with-distill` - 提炼 + 归档
- 更新 `tools/session-archive` - 使用新流程

### 3. 无需修改的文件
- `~/.openviking/ov.conf` - 配置已正确
- `scripts/openviking_archive_entry.py` - 脚本已存在
- OpenClaw 核心代码 - 无需修改

## 默认值

| 配置项 | 默认值 | 启用值 | 回退值 |
|-------|--------|--------|--------|
| OpenViking 服务 | stopped | running | stopped |
| session-archive | 原始流程 | distill 流程 | 恢复 .original |
| embedding provider | N/A | ollama/mxbai | N/A |

## 回滚方式

```bash
# 回滚到原始归档流程
cp ~/.openclaw/workspace/tools/session-archive.original ~/.openclaw/workspace/tools/session-archive

# 停止 OpenViking 服务
pkill -f openviking
```

