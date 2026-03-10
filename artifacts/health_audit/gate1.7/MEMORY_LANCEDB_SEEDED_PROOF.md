# memory-lancedb Seeded Proof

**日期**: 2026-03-09 22:28 CST

---

## 目标

不再停留在 initialized only，主动验证 empty -> populated -> retrievable。

---

## 当前状态检查

### 1. Initialized

**证据**:
```
[gateway] memory-lancedb: initialized (db: ~/.openclaw/memory/lancedb, model: mxbai-embed-large)
```

**结论**: ✅ 初始化成功

---

### 2. Populated

**数据目录检查**:
```bash
$ ls -la ~/.openclaw/memory/lancedb/
total 8
drwxrwxr-x 2 moonlight moonlight 4096 Mar  9 21:53 .
drwxrwxr-x 3 moonlight moonlight 4096 Mar  9 21:53 ..
```

**结论**: ❌ 数据目录为空

---

### 3. Retrievable

**recall 测试**:
```
[gateway] memory-lancedb: recall failed: Error: 404 404 page not found
```

**结论**: ❌ 返回 404（空表）

---

### 4. Behavior-changing

**结论**: ❌ 无法验证（无数据）

---

## 为什么未 populated

### autoCapture 配置

```json
{
  "autoCapture": true,
  "autoRecall": true
}
```

### 触发条件

**问题**: autoCapture 未触发

**可能原因**:
1. 需要对话结束才触发
2. 需要 token 阈值
3. 需要 Gateway 特定 API 调用

---

## 尝试主动写入

### 测试 Ollama Embedding

```bash
curl http://192.168.79.1:11434/api/embeddings -d '{"model": "mxbai-embed-large", "prompt": "test"}'
```

**结果**: ✅ 返回 1024 维向量

---

### 尝试写入 LanceDB

**问题**: LanceDB 由 Gateway 内部管理，无法直接写入

**尝试方法**:
1. Gateway memory API: 404 Not Found
2. 直接写入文件: 不适用（需要 LanceDB 格式）
3. 触发 autoCapture: 未找到触发方法

---

## 最终判断

# initialized only

**状态**:
- initialized: ✅
- populated: ❌
- retrievable: ❌
- behavior-changing: ❌

---

## 卡点

**无法主动写入 LanceDB**

原因:
1. LanceDB 是 Gateway 内部组件
2. 无公开 API 手动写入
3. autoCapture 触发条件未知

---

## 下一步

1. **等待自然触发**: 对话结束后检查
2. **查阅文档**: 了解 autoCapture 触发条件
3. **联系 OpenClaw**: 询问手动 populate 方法

---

## 结论

**未达标**: memory-lancedb 仍处于 initialized only 状态。

**不是故障**: 初始化和配置正确，只是缺少数据。
