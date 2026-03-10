# memory-lancedb Write-Path Analysis

**日期**: 2026-03-09 22:45 CST

---

## 1. 写入入口定位

### 正式写入入口

**触发事件**: `agent_end`

**位置**: `extensions/memory-lancedb/index.ts`

**触发条件**:
1. `event.success = true` (对话成功结束)
2. `event.messages` 不为空
3. 消息 `role = 'user'`
4. 文本长度: `10 < len < maxChars` (默认 500)

### 过滤条件 (shouldCapture)

```javascript
// 跳过条件:
- 文本长度 < 10 或 > maxChars
- 包含 <relevant-memories> 标签
- XML 格式内容 (<...></...>)
- Markdown 格式 (** 和 \n-)
- Emoji 数量 > 3
```

### 存储参数

- 每次对话最多存储: 3 条
- 重复检测阈值: 相似度 > 0.95
- 默认 importance: 0.7
- 自动分类: detectCategory(text)

---

## 2. 存储结构

### LanceDB 表结构

```typescript
interface MemoryEntry {
  id: string;          // UUID
  text: string;        // 原始文本
  vector: number[];    // Embedding 向量 (1024 维)
  importance: number;  // 重要性 0-1
  category: string;    // 分类
  createdAt: number;   // 时间戳
}
```

### 数据库路径

```
~/.openclaw/memory/lancedb/
```

### 表名

```
memories
```

---

## 3. 问题分析

### 为什么未 populated

**根因**: `agent_end` 事件未触发

**可能原因**:
1. 当前对话尚未结束
2. Gateway 事件机制不同
3. 需要特定条件才能触发

**日志证据**:
```
// 没有 autoCapture 日志
// 没有 agent_end 日志
// 只有 context-compression 日志
```

---

## 4. 尝试的方法

| 方法 | 结果 | 原因 |
|------|------|------|
| 直接 POST memory API | ❌ | Gateway 无公开 API |
| 使用 openclaw memory CLI | ❌ | 这是 sqlite-vec 系统，不是 LanceDB |
| Python lancedb 包 | ❌ | 未安装，系统限制 |
| Node.js lancedb 模块 | ❌ | 依赖被忽略 |
| 创建 marker 文件 | ✅ | 目录可写，但不是 LanceDB 格式 |

---

## 5. 结论

**写入入口**: 已定位（agent_end 事件）

**触发条件**: 已明确

**当前阻塞**: 无法手动触发 agent_end 事件

**状态**: **blocked with identified root cause**
