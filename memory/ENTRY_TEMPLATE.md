# Memory Entry Template

## 元数据头 (YAML)

```markdown
---
id: mem_YYYYMMDD_XXX
type: RULE | FACT | PREFERENCE | REFLECTION
scope: global | projects/{name} | domains/{name}
tier: HOT | WARM | COLD
created_at: YYYY-MM-DD
last_used: YYYY-MM-DD
use_count: N
correction_count: N
confidence: 0.0-1.0
importance: 0.0-1.0 (default 0.5)
pinned: false
conflict_penalty: 0.0
sources:
  - session: YYYY-MM-DD
    evidence: "..."
    task_id: "..."
---
```

## 条目正文

规则/事实/偏好/反思内容...

## 示例

```markdown
---
id: mem_20260303_001
type: RULE
scope: projects/openemotion
tier: WARM
created_at: 2026-03-03
last_used: 2026-03-03
use_count: 1
correction_count: 3
confidence: 0.85
importance: 0.7
pinned: false
conflict_penalty: 0.0
sources:
  - session: 2026-03-03
    evidence: "No, use sorted(set) not list(set) for cross-process stability"
    task_id: "mvp8_implementation"
---

## Hash Determinism: 使用 sorted(set)

set/frozenset 的迭代顺序受 PYTHONHASHSEED 影响，跨进程不稳定。
必须使用 `sorted(set)` 确保一致性。

### 触发场景
- 需要跨进程 deterministic 的 hash 计算
- JSON 字段列表输出

### 相关
- MVP-8.2 实现
- Commit: 2abda02
```
