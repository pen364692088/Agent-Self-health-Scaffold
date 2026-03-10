# memory-lancedb Recall Proof

**日期**: 2026-03-09 22:45 CST

---

## Recall 测试

### 测试 1: 检查当前 recall 状态

**命令**:
```bash
curl -s http://127.0.0.1:18789/v1/memory/recall -d '{"query": "test"}'
```

**结果**: ❌ 404 Not Found

**原因**: Gateway 未暴露公开 API

---

### 测试 2: 使用 Gateway 内置 recall

**命令**:
```bash
# 通过 Gateway 内部调用
```

**结果**: ❌ 404 page not found

**日志**:
```
[gateway] memory-lancedb: recall failed: Error: 404 404 page not found
```

**原因**: LanceDB 表为空

---

### 测试 3: 验证 marker 文件

**检查**:
```bash
ls -la ~/.openclaw/memory/lancedb/
```

**结果**:
```
- gate1_7_seed_marker.json (marker file)
```

**限制**: marker 文件不是 LanceDB 格式，无法被 recall

---

## 结论

**Recall 状态**: ❌ 失败

**原因**: 
1. LanceDB 表为空
2. 无公开 API
3. 无法手动写入数据

**验证状态**: **无法验证**
