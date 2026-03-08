# Context Ratio Source v1.1.1

## Overview

本文档定义了 Context Ratio 的获取方式和 fallback 策略。

## Primary Source

**OpenClaw session_status**

```bash
session_status
```

输出格式：
```
Context: X/Y (Z%)
```

解析方法：
```python
import re
match = re.search(r'Context:\s*\d+/(\d+)\s*\((\d+)%\)', output)
if match:
    max_tokens = int(match.group(1))
    percentage = int(match.group(2))
    ratio = percentage / 100
```

## Fallback Sources

### Fallback 1: Estimate from File Size

如果 session_status 不可用，基于会话文件大小估算：

```python
session_file = "~/.openclaw/agents/main/sessions/<session_id>.jsonl"
file_size = os.path.getsize(session_file)
# Rough estimate: 1 token ≈ 4 bytes
estimated_tokens = file_size / 4
# Assume max 200k tokens
ratio = min(estimated_tokens / 200000, 1.0)
```

### Fallback 2: Default Safe Value

如果无法估算，使用保守值：

```python
# Assume 50% to be safe
ratio = 0.5
degraded_mode = True
```

## Threshold Behavior

| Ratio | Status | Action |
|-------|--------|--------|
| < 0.60 | Normal | Event-triggered writes |
| 0.60 - 0.80 | Warning | Check before each reply |
| > 0.80 | Critical | Force handoff + flush |

## Implementation

```python
def get_context_ratio() -> tuple[float, bool]:
    """
    Get context ratio with fallback.
    Returns: (ratio, degraded_mode)
    """
    # Try primary source
    try:
        result = subprocess.run(
            ["session_status"],
            capture_output=True, text=True, timeout=5
        )
        match = re.search(r'Context:\s*\d+/(\d+)\s*\((\d+)%\)', result.stdout)
        if match:
            percentage = int(match.group(2))
            return percentage / 100, False
    except:
        pass
    
    # Fallback 1: File size estimate
    try:
        session_files = list(Path("~/.openclaw/agents/main/sessions").glob("*.jsonl"))
        if session_files:
            latest = max(session_files, key=lambda f: f.stat().st_mtime)
            file_size = latest.stat().st_size
            estimated_tokens = file_size / 4
            ratio = min(estimated_tokens / 200000, 1.0)
            return ratio, True
    except:
        pass
    
    # Fallback 2: Default
    return 0.5, True
```

## Logging

每次获取 ratio 时记录：
```json
{
  "timestamp": "2026-03-07T20:00:00",
  "source": "session_status",
  "ratio": 0.35,
  "degraded_mode": false
}
```

如果是 degraded_mode，应标记：
```json
{
  "timestamp": "2026-03-07T20:00:00",
  "source": "fallback_file_size",
  "ratio": 0.25,
  "degraded_mode": true,
  "warning": "session_status unavailable, using fallback"
}
```

---
Version: 1.1.1
Created: 2026-03-07