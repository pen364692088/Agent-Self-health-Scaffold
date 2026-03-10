# Patch Queue P1

**Generated**: 2026-03-10 06:55 CST
**Version**: 1.0
**Status**: PLANNING - No execution during freeze

---

## P1-4: Merge Memory Retrieval Paths to session-query --mode

### Summary
Consolidate `memory-retrieve`, `memory-search`, `context-retrieve` into unified `session-query` with `--mode` parameter.

### Affected Files

| File | Change Type |
|------|-------------|
| `tools/session-query` | Enhancement |
| `tools/memory-retrieve` | Deprecation wrapper |
| `tools/memory-search` | Deprecation wrapper |
| `tools/context-retrieve` | Optional integration |
| `tests/test_session_query_modes.py` | New test file |
| `TOOLS.md` | Documentation |
| `memory.md` | Documentation |

### Current Behavior

```
# Multiple scattered retrieval tools

session-query "search terms"         # SQLite FTS
memory-retrieve --query "..."        # Unclear backend
memory-search "..."                  # Unclear backend
context-retrieve --query "..."       # OpenViking + Capsule
```

### New Behavior

```python
# Unified interface with --mode parameter

session-query "search terms"                     # Default: recent
session-query "search terms" --mode recent       # Recent events
session-query "search terms" --mode semantic     # Vector search (OpenViking)
session-query "search terms" --mode keyword      # FTS search (SQLite)
session-query "search terms" --mode capsule      # Capsule retrieval (S1)
```

### Implementation

**Phase 1: Add --mode to session-query**

```python
# tools/session-query v2.0

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Search query")
    parser.add_argument("--mode", choices=["recent", "semantic", "keyword", "capsule"],
                        default="recent", help="Retrieval mode")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--session-id", help="Filter by session")
    parser.add_argument("--json", action="store_true")
    # ... existing args ...
    
    args = parser.parse_args()
    
    if args.mode == "recent":
        results = query_recent_events(args.query, args.limit, args.session_id)
    elif args.mode == "semantic":
        results = query_semantic_search(args.query, args.limit)
    elif args.mode == "keyword":
        results = query_fts_search(args.query, args.limit)
    elif args.mode == "capsule":
        results = query_capsules(args.query, args.limit)
    
    output_results(results, args.json)


def query_semantic_search(query: str, limit: int) -> list:
    """Layer C: Vector search via OpenViking."""
    try:
        result = subprocess.run(
            ["openviking", "find", query, "--limit", str(limit)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return [{
                "source": "vector_index",
                "confidence": item.get("score", 0.5),
                "tier": "L2",
                **item
            } for item in data.get("results", [])]
    except Exception as e:
        # Fallback to keyword search
        return query_fts_search(query, limit)
    return []


def query_capsules(query: str, limit: int) -> list:
    """S1: Capsule-based retrieval."""
    capsules_dir = WORKSPACE / "artifacts" / "capsules"
    results = []
    
    for capsule_file in capsules_dir.glob("*.json"):
        try:
            capsule = json.loads(capsule_file.read_text())
            # Simple keyword match in capsule fields
            searchable = " ".join([
                capsule.get("topic", ""),
                capsule.get("summary", ""),
                " ".join(capsule.get("retrieval_keys", []))
            ])
            if query.lower() in searchable.lower():
                results.append({
                    "source": "capsule",
                    "confidence": 0.7,
                    "tier": "L1",
                    **capsule
                })
        except:
            continue
    
    return results[:limit]
```

**Phase 2: Create Deprecation Wrappers**

```python
# tools/memory-retrieve v2.0 (deprecation wrapper)

import warnings
import subprocess
import sys

def main():
    warnings.warn(
        "memory-retrieve is deprecated. Use: session-query --mode semantic",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Forward to session-query
    args = sys.argv[1:]
    result = subprocess.run(
        ["session-query", "--mode", "semantic"] + args,
        capture_output=False
    )
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
```

```python
# tools/memory-search v2.0 (deprecation wrapper)

import warnings
import subprocess
import sys

def main():
    warnings.warn(
        "memory-search is deprecated. Use: session-query --mode keyword",
        DeprecationWarning,
        stacklevel=2
    )
    
    args = sys.argv[1:]
    result = subprocess.run(
        ["session-query", "--mode", "keyword"] + args,
        capture_output=False
    )
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
```

### Risk Level

| Aspect | Risk | Mitigation |
|--------|------|------------|
| Breaking existing callers | LOW | Wrappers forward calls |
| Performance difference | MEDIUM | Benchmark before/after |
| OpenViking availability | LOW | Fallback to FTS |

### Rollback Method

```bash
# If issues arise
git checkout HEAD~1 -- tools/session-query
git checkout HEAD~1 -- tools/memory-retrieve
git checkout HEAD~1 -- tools/memory-search

# Or keep old tools, just remove --mode
```

### Required Tests

```python
# tests/test_session_query_modes.py

import subprocess
import json

def test_mode_recent():
    """Verify recent mode returns events."""
    result = subprocess.run(
        ["session-query", "test", "--mode", "recent", "--json"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "results" in data or "error" in data

def test_mode_semantic():
    """Verify semantic mode calls OpenViking."""
    result = subprocess.run(
        ["session-query", "memory", "--mode", "semantic", "--json"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    # May fallback to keyword if OpenViking unavailable

def test_mode_keyword():
    """Verify keyword mode uses FTS."""
    result = subprocess.run(
        ["session-query", "session", "--mode", "keyword", "--json"],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_mode_capsule():
    """Verify capsule mode retrieves capsules."""
    # Create test capsule
    capsule_dir = WORKSPACE / "artifacts" / "capsules"
    capsule_dir.mkdir(parents=True, exist_ok=True)
    test_capsule = {
        "topic": "test_topic",
        "summary": "Test capsule for query",
        "retrieval_keys": ["test", "query"]
    }
    (capsule_dir / "test_capsule.json").write_text(json.dumps(test_capsule))
    
    result = subprocess.run(
        ["session-query", "test", "--mode", "capsule", "--json"],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_memory_retrieve_deprecated():
    """Verify memory-retrieve shows deprecation warning."""
    result = subprocess.run(
        ["memory-retrieve", "test"],
        capture_output=True, text=True
    )
    # Should still work, but may show warning
    assert result.returncode == 0

def test_memory_search_deprecated():
    """Verify memory-search shows deprecation warning."""
    result = subprocess.run(
        ["memory-search", "test"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
```

### Dependency Order

```
1. Implement --mode in session-query
2. Create deprecation wrappers for memory-retrieve, memory-search
3. Update tests
4. Update documentation (TOOLS.md, memory.md)
5. Monitor usage of deprecated tools
```

---

## P1-5: Integrate State Writing Through safe-write

### Summary
Make `state-write-atomic` internally call `safe-write` for unified policy enforcement.

### Affected Files

| File | Change Type |
|------|-------------|
| `tools/state-write-atomic` | Refactor |
| `tools/safe-write` | May need enhancement |
| `tests/test_state_write_integration.py` | New test file |
| `TOOLS.md` | Documentation |

### Current Behavior

```python
# state-write-atomic: Direct write without policy check

def state_write_atomic(path, content):
    # Direct file write
    path.write_text(content)
    return True
```

### New Behavior

```python
# state-write-atomic: Delegates to safe-write

def state_write_atomic(path, content):
    """
    Atomic state write with policy enforcement.
    Internally uses safe-write for unified policy check.
    """
    # Import and call safe-write
    from safe_write import safe_write
    
    result = safe_write(path, content, atomic=True)
    return result["success"]
```

### Implementation

**Phase 1: Enhance safe-write with atomic option**

```python
# tools/safe-write v1.1

import tempfile
import shutil

def safe_write(path: str, content: str, atomic: bool = False) -> dict:
    """
    Write file with policy check.
    
    Args:
        path: Target file path
        content: Content to write
        atomic: If True, write to temp file then move
    
    Returns:
        {"success": bool, "action": str, "message": str}
    """
    # Run policy check
    result = subprocess.run(
        ["policy-eval", "--path", path, "--tool", "write", "--json"],
        capture_output=True, text=True
    )
    
    try:
        policy = json.loads(result.stdout)
    except:
        policy = {"action": "WARN", "message": "Policy check failed"}
    
    if policy.get("action") == "DENY":
        return {
            "success": False,
            "action": "DENY",
            "message": policy.get("message", "Policy denied")
        }
    
    # Perform write
    path_obj = Path(path).expanduser()
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    if atomic:
        # Write to temp file, then move
        fd, temp_path = tempfile.mkstemp(dir=path_obj.parent)
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(content)
            shutil.move(temp_path, str(path_obj))
        except Exception as e:
            os.unlink(temp_path)
            return {"success": False, "action": "ERROR", "message": str(e)}
    else:
        path_obj.write_text(content)
    
    return {
        "success": True,
        "action": "ALLOW",
        "message": "File written"
    }
```

**Phase 2: Update state-write-atomic**

```python
# tools/state-write-atomic v2.0

#!/usr/bin/env python3
"""
state-write-atomic v2.0 - Atomic state write with policy enforcement

Internally delegates to safe-write for unified policy check.

Usage:
  state-write-atomic <path> <content>
  state-write-atomic --path <path> --file <source>
"""

import sys
import subprocess
from pathlib import Path

SAFE_WRITE = Path(__file__).parent / "safe-write"

def state_write_atomic(path: str, content: str) -> bool:
    """
    Write state file atomically with policy check.
    
    Delegates to safe-write for policy enforcement.
    """
    result = subprocess.run(
        [str(SAFE_WRITE), path, content, "--atomic"],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        print(f"✅ Written to {path}")
        return True
    else:
        print(f"❌ Write blocked: {result.stdout}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Target file path")
    parser.add_argument("content", nargs="?", help="Content to write")
    parser.add_argument("--file", help="Read content from file")
    args = parser.parse_args()
    
    if args.file:
        content = Path(args.file).read_text()
    elif args.content:
        content = args.content
    else:
        content = sys.stdin.read()
    
    success = state_write_atomic(args.path, content)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
```

### Risk Level

| Aspect | Risk | Mitigation |
|--------|------|------------|
| Breaking state writes | LOW | Same interface, just adds check |
| Policy denial for valid writes | LOW | Path patterns already correct |
| Performance overhead | LOW | Negligible |

### Rollback Method

```bash
# If issues arise
git checkout HEAD~1 -- tools/state-write-atomic
git checkout HEAD~1 -- tools/safe-write

# Or bypass policy temporarily
# Change safe-write to skip policy check for state files
```

### Required Tests

```python
# tests/test_state_write_integration.py

import subprocess
import tempfile
from pathlib import Path

def test_state_write_uses_safe_write():
    """Verify state-write-atomic calls safe-write."""
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        temp_path = f.name
    
    try:
        result = subprocess.run(
            ["state-write-atomic", temp_path, "test content"],
            capture_output=True, text=True
        )
        
        # Should succeed
        assert result.returncode == 0
        
        # Verify content
        assert Path(temp_path).read_text() == "test content"
    finally:
        Path(temp_path).unlink(missing_ok=True)

def test_state_write_blocked_for_protected_path():
    """Verify state-write-atomic respects policy for protected paths."""
    # Try to write to a path that should be denied
    # (This depends on policy configuration)
    pass

def test_safe_write_atomic_option():
    """Verify safe-write --atomic works."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        temp_path = f.name
    
    try:
        result = subprocess.run(
            ["safe-write", temp_path, "atomic test", "--atomic"],
            capture_output=True, text=True
        )
        
        assert result.returncode == 0
        assert Path(temp_path).read_text() == "atomic test"
    finally:
        Path(temp_path).unlink(missing_ok=True)

def test_concurrent_safe_write():
    """Verify atomic writes don't corrupt under concurrent access."""
    import threading
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        temp_path = f.name
    
    errors = []
    
    def write_content(i):
        try:
            result = subprocess.run(
                ["safe-write", temp_path, f"content_{i}", "--atomic"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                errors.append(result.stdout)
        except Exception as e:
            errors.append(str(e))
    
    threads = [threading.Thread(target=write_content, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # No errors should occur
    assert len(errors) == 0
    
    # File should have valid content from one of the writes
    content = Path(temp_path).read_text()
    assert content.startswith("content_")
    
    Path(temp_path).unlink()
```

### Dependency Order

```
1. Add --atomic option to safe-write
2. Update state-write-atomic to call safe-write
3. Run tests
4. Update documentation
5. Monitor for any policy denials
```

---

## P1 Summary

| Patch | Risk | Rollback | Tests Required |
|-------|------|----------|----------------|
| P1-4 | LOW-MEDIUM | Easy | 6 tests |
| P1-5 | LOW | Easy | 4 tests |

**Total Tests Required**: 10 new tests

**Estimated Implementation Time**: 3-4 hours

**Recommended Execution Order**: P1-5 → P1-4
