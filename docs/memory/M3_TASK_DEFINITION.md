# M3: Unified Query Service

**Status**: In Progress
**Branch**: feature/memory-kernel-m3
**Started**: 2026-03-15T23:27:00Z

---

## Objective

提供统一查询服务层，不迁移、不删旧链、不接管 truth source、不强上 LanceDB。

---

## Scope

### In Scope
- keyword search
- metadata filter
- scope filter
- authority-aware ranking
- top-k recall
- trace 输出

### Out of Scope
- 数据迁移
- 删除旧链
- 接管 truth source
- 强制 LanceDB 接入

---

## Deliverables

| File | Description |
|------|-------------|
| core/memory/memory_service.py | 统一服务入口 |
| core/memory/memory_search.py | 搜索引擎 |
| core/memory/memory_ranker.py | 排序器 |
| core/memory/memory_scope.py | Scope 过滤器 |
| tests/memory/test_memory_search.py | 测试套件 |

---

## Architecture

```
memory_service.py (Facade)
    ├── memory_search.py (Search Engine)
    │   ├── keyword_match
    │   ├── metadata_filter
    │   └── scope_filter
    ├── memory_ranker.py (Ranker)
    │   └── authority_aware_ranking
    └── memory_scope.py (Scope Handler)
```

---

## API Design

### MemoryService

```python
class MemoryService:
    def search(
        query: str,
        scope: Optional[MemoryScope] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        trace: bool = False
    ) -> SearchResult:
        """
        统一查询入口
        
        Args:
            query: 关键词查询
            scope: 作用域过滤 (GLOBAL/PROJECTS/DOMAINS)
            filters: 元数据过滤
            top_k: 返回数量
            trace: 是否输出追踪信息
        
        Returns:
            SearchResult: 包含 records 和 trace_info
        """
```

### SearchResult

```python
@dataclass
class SearchResult:
    records: List[MemoryRecord]
    total_count: int
    trace_info: Optional[Dict[str, Any]] = None
```

---

## Test Requirements

- test_keyword_search_basic
- test_keyword_search_with_scope_filter
- test_metadata_filter
- test_scope_filter_projects
- test_scope_filter_domains
- test_authority_aware_ranking
- test_top_k_limit
- test_trace_output
- test_empty_query
- test_no_results

---

## Acceptance Criteria

1. 所有测试通过
2. 不依赖 LanceDB（可插拔）
3. 支持所有 6 项核心功能
4. trace 输出可验证
5. 独立分支/提交/测试

---

## Progress

- [ ] core/memory/memory_scope.py
- [ ] core/memory/memory_ranker.py
- [ ] core/memory/memory_search.py
- [ ] core/memory/memory_service.py
- [ ] tests/memory/test_memory_search.py
- [ ] Acceptance

---

**Updated**: 2026-03-15T23:27:00Z
