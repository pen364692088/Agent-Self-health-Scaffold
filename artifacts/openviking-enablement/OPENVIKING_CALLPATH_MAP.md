# OpenViking Callpath Map

## 入口点

### 1. 命令行工具
```bash
openviking serve --config ~/.openviking/ov.conf  # 启动服务
openviking add-resource <file> --to <uri>        # 添加资源
openviking find <query> -u <uri>                 # 检索
```

### 2. Python 脚本
- `scripts/openviking_archive_entry.py` - 归档入口
- `scripts/openviking_backfill_embeddings.py` - 向量回填
- `scripts/openviking_ingest_index.py` - 索引入库

### 3. HTTP API
- `GET /health` - 健康检查
- `POST /add-resource` - 添加资源
- `POST /find` - 检索

## 当前集成点

### session-archive (已更新)
```
session-archive 
  → archive-with-distill 
  → distill-content (提炼)
  → openviking_archive_entry.py (入库)
  → OpenViking 服务
```

### compaction-archive hook
```
after_compaction hook
  → session-archive
  → (同上)
```

## 控制点

| 控制项 | 位置 | 当前值 |
|-------|------|--------|
| 服务配置 | ~/.openviking/ov.conf | 已配置 |
| Embedding API | ov.conf → api_base | http://192.168.79.1:11434/v1 |
| 归档脚本 | scripts/openviking_archive_entry.py | 已存在 |
| session-archive | tools/session-archive | 已更新为 distill 流程 |

## 与 Compaction 的关系

**完全独立**：
- OpenViking = 向量存储 + 检索
- Compaction = 上下文压缩

**唯一交集**: `after_compaction` hook 可触发归档，但这是可选的副作用。

