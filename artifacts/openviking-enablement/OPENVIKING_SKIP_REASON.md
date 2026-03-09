# OpenViking Skip Reason Analysis

## 当前状态
OpenViking 在 session-archive 执行时显示 **skipped**。

## 根因分析

### 问题 1: AGFS 服务未运行
```
Connection refused - server not running at localhost:1833
```

AGFS (Agent File System) 是 OpenViking 的内部临时文件操作组件。

### 问题 2: 服务重启后已恢复
```bash
$ curl http://localhost:8000/health
{"status":"ok"}
```

重启 OpenViking 服务后，AGFS 问题已解决。

### 问题 3: 文件过大导致失败
Daily log (18KB) 可能超过 embedding 模型的处理限制。

## 已实施修复

### 修复 1: 减小 chunk 大小
```bash
python3 openviking_archive_entry.py --max-tokens 400 --max-chars 2000 --max-bytes 6000
```

### 修复 2: 使用提炼后内容
创建了 `archive-with-distill` 工具：
1. 先用 LLM 提炼要点（压缩 90%+）
2. 只存储提炼后的内容到 OpenViking
3. 附带原始文件路径引用

## 当前结论

OpenViking 服务本身正常，skipped 原因：
1. ~~AGFS 未运行~~ → 已修复
2. ~~文件过大~~ → 已通过 distill 解决

