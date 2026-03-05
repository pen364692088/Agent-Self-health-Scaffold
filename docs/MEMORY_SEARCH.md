# Agent Memory Search Guide

All agents can search past sessions using qmd.

## Quick Start

```bash
# Search your own memory (auto-detected agent)
memory-search "workflow model config"

# Search with limit
memory-search "docker setup" --limit 5

# Global search (all agents)
memory-search "deployment" --global

# Specify agent explicitly
memory-search "bug fix" --agent developer
```

## How It Works

- All sessions are indexed in the `sessions` collection
- Searches use BM25 + vector hybrid ranking
- Results include session ID and relevant snippets

## Use Cases

1. **Recall past solutions:**
   ```bash
   memory-search "how to fix npm install error"
   ```

2. **Find similar tasks:**
   ```bash
   memory-search "antfarm workflow configuration"
   ```

3. **Check previous decisions:**
   ```bash
   memory-search "why chose ollama for heartbeat"
   ```

## Tips

- Use natural language queries (not just keywords)
- Try synonyms if first search doesn't find results
- Combine with `qmd get` to read full session:
  ```bash
  qmd get sessions/<session-id>.jsonl:10 -l 50
  ```
