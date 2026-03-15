# Memory Contract

## 概述

本文档定义 Memory Kernel 的统一契约，所有记忆相关操作必须遵循此契约。

## 核心类型

### MemoryRecord

```python
@dataclass
class MemoryRecord:
    """统一记忆记录"""
    id: str                    # 唯一标识
    content: str               # 内容
    source_kind: MemorySourceKind  # 来源类型
    scope: MemoryScope         # 范围
    authority_level: str       # truth | knowledge | retrieval
    tags: List[str]            # 标签
    confidence: float          # 置信度 0-1
    importance: float          # 重要性 0-1
    retention: RetentionPolicy # 保留策略
    
    created_at: str            # 创建时间
    updated_at: str            # 更新时间
    source_path: str           # 来源文件路径
    source_ref: str            # 来源引用
    
    retrieval_eligibility: bool    # 是否可召回
    capture_reason: Optional[str]  # 捕获原因
    recall_reason: Optional[str]   # 召回原因
```

### MemorySourceKind

```python
class MemorySourceKind(Enum):
    """记忆来源类型"""
    LEDGER = "ledger"           # Truth 层
    TASK_STATE = "task_state"   # Truth 层
    CHECKPOINT = "checkpoint"   # Truth 层
    
    USER_PREFERENCE = "user_preference"   # Knowledge 层
    PROJECT_RULE = "project_rule"         # Knowledge 层
    DECISION = "decision"                 # Knowledge 层
    TRUST_ANCHOR = "trust_anchor"         # Knowledge 层
    
    DAILY_NOTE = "daily_note"   # Retrieval 层
    SESSION_LOG = "session_log" # Retrieval 层
    DOCUMENTATION = "docs"      # Retrieval 层
```

### MemoryScope

```python
@dataclass
class MemoryScope:
    """记忆范围"""
    project: Optional[str]      # 项目名
    session: Optional[str]      # 会话 ID
    task: Optional[str]         # 任务 ID
    user: Optional[str]         # 用户 ID
    global_scope: bool = False  # 全局范围
```

### RetentionPolicy

```python
@dataclass
class RetentionPolicy:
    """保留策略"""
    ttl_days: Optional[int]     # 存活天数，None 表示永久
    hot_tier_days: int = 30     # HOT 分层天数
    warm_tier_days: int = 90    # WARM 分层天数
    decay_factor: float = 0.9   # 衰减因子
    promote_on_access: bool = True  # 访问时晋升
```

### ConflictResolutionPolicy

```python
class ConflictResolutionPolicy(Enum):
    """冲突解决策略"""
    AUTHORITY_WINS = "authority_wins"     # 按权威层级
    RECENCY_WINS = "recency_wins"         # 按时间新旧
    CONFIDENCE_WINS = "confidence_wins"   # 按置信度
    MANUAL_REVIEW = "manual_review"       # 人工审核
```

## 操作契约

### Store 契约

```python
def store(record: MemoryRecord) -> str:
    """
    存储记忆记录
    
    前置条件:
    - record.id 唯一
    - record.authority_level 已分类
    - record.scope 已设置
    
    后置条件:
    - 记录持久化成功
    - 返回记录 ID
    - 冲突已记录
    """
```

### Search 契约

```python
def search(query: MemorySearchQuery) -> MemorySearchResult:
    """
    搜索记忆
    
    前置条件:
    - query 有至少一个过滤条件
    - 返回结果数量有上限
    
    后置条件:
    - 结果按 authority + relevance 排序
    - 每条结果有 recall_reason
    - Truth 记录只精确匹配
    """
```

### Capture 契约

```python
def capture(content: str, context: CaptureContext) -> Optional[str]:
    """
    捕获记忆
    
    前置条件:
    - content 符合白名单规则
    - 不在黑名单中
    
    后置条件:
    - 新记录进入 pending 状态
    - capture_reason 已记录
    - 未经确认不晋升
    """
```

## 验证规则

### 记录完整性

| 字段 | 必需 | 验证 |
|------|------|------|
| id | 是 | UUID 格式 |
| content | 是 | 非空 |
| source_kind | 是 | 枚举值 |
| authority_level | 是 | truth/knowledge/retrieval |
| scope | 是 | 非空对象 |
| created_at | 是 | ISO8601 |
| source_path | 是 | 文件存在 |

### 权威级别约束

| authority_level | 允许的 source_kind |
|-----------------|-------------------|
| truth | ledger, task_state, checkpoint |
| knowledge | user_preference, project_rule, decision, trust_anchor |
| retrieval | daily_note, session_log, docs |

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-15 | 初始契约定义 |
