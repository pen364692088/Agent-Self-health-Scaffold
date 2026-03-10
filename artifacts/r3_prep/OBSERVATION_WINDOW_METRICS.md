# Observation Window Metrics

**Generated**: 2026-03-10 06:40 CST
**Version**: 1.0
**Observation Period**: 2026-03-10 05:28 ~ 2026-03-17 05:28

---

## 1. Memory-LanceDB Metrics

### Collection Method

```bash
# Daily collection (automated)
~/.openclaw/workspace/tools/memory-daily-obs

# Manual collection
lancedb-query --count
grep -c "shouldCapture" logs/openclaw.log
```

### Metrics Table

| Metric | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 |
|--------|-------|-------|-------|-------|-------|-------|-------|
| Row count | 2 | | | | | | |
| autoCapture hits | N/A | | | | | | |
| recall injections | 87 | | | | | | |
| false captures | 0 | | | | | | |
| duplicate captures | 0 | | | | | | |
| embedding errors | 0 | | | | | | |

### Exit Criteria

| Criteria | Target | Current | Status |
|----------|--------|---------|--------|
| false captures | 0 | 0 | ✅ |
| duplicate captures | 0 | 0 | ✅ |
| embedding errors | 0 | 0 | ✅ |
| recall success rate | > 90% | TBD | ⏳ |
| autoCapture relevance | > 80% | TBD | ⏳ |

---

## 2. Execution Policy Metrics

### Collection Method

```bash
# Daily collection
~/.openclaw/workspace/tools/policy-daily-check --json

# Violation summary
~/.openclaw/workspace/tools/policy-violation-summary --hours 24 --json
```

### Metrics Table

| Metric | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 |
|--------|-------|-------|-------|-------|-------|-------|-------|
| Total violations | TBD | | | | | | |
| DENY samples | TBD | | | | | | |
| WARN samples | TBD | | | | | | |
| Policy eval calls | TBD | | | | | | |
| Bypass attempts | TBD | | | | | | |

### Sample Maturity

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| DENY samples | >= 5 | TBD | ⏳ |
| WARN samples | >= 10 | TBD | ⏳ |
| Sample diversity | >= 3 paths | TBD | ⏳ |

---

## 3. verify-and-close Enforcement Metrics

### Collection Method

```bash
# Check receipts
ls -la ~/.openclaw/workspace/artifacts/receipts/

# Count enforcement
grep -c "READY_TO_CLOSE\|BLOCKED" logs/verify_and_close.log 2>/dev/null
```

### Metrics Table

| Metric | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 |
|--------|-------|-------|-------|-------|-------|-------|-------|
| verify-and-close calls | TBD | | | | | | |
| READY_TO_CLOSE | TBD | | | | | | |
| BLOCKED | TBD | | | | | | |
| Receipts created | TBD | | | | | | |
| finalize-response calls | TBD | | | | | | |

### Enforcement Rate

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Tasks with receipts | 100% | TBD | ⏳ |
| BLOCKED resolved | 100% | TBD | ⏳ |
| Fake completion blocked | 100% | TBD | ⏳ |

---

## 4. Callback and Inbox Metrics

### Collection Method

```bash
# Inbox metrics
~/.openclaw/workspace/tools/subagent-inbox-metrics --json

# Callback delivery probe
~/.openclaw/workspace/tools/probe-callback-delivery --json
```

### Metrics Table

| Metric | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 |
|--------|-------|-------|-------|-------|-------|-------|-------|
| Pending receipts | TBD | | | | | | |
| Processed receipts | TBD | | | | | | |
| Avg receipt age (min) | TBD | | | | | | |
| Callback delivery rate | TBD | | | | | | |
| Stuck claims | TBD | | | | | | |

### Health Indicators

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Pending count | < 5 | TBD | ⏳ |
| Receipt age p95 | < 30 min | TBD | ⏳ |
| Stuck claims | 0 | TBD | ⏳ |

---

## 5. Session Continuity Metrics

### Collection Method

```bash
# Daily check
~/.openclaw/workspace/tools/session-continuity-daily-check --json

# Parse events
~/.openclaw/workspace/tools/parse-continuity-events --today
```

### Metrics Table

| Metric | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 |
|--------|-------|-------|-------|-------|-------|-------|-------|
| Recovery success | TBD | | | | | | |
| Recovery failure | TBD | | | | | | |
| Handoff created | TBD | | | | | | |
| High context events | TBD | | | | | | |
| WAL entries | TBD | | | | | | |

### Continuity Health

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Recovery success rate | > 95% | TBD | ⏳ |
| Handoff coverage | 100% | TBD | ⏳ |
| Uncertainty events | 0 | TBD | ⏳ |

---

## 6. Heartbeat Probe Metrics

### Collection Method

```bash
# Run all probes
for probe in probe-*; do
    echo "=== $probe ===" 
    ~/.openclaw/workspace/tools/$probe --json 2>/dev/null | head -5
done
```

### Probe Status Table

| Probe | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 |
|-------|-------|-------|-------|-------|-------|-------|-------|
| probe-execution-policy-v2 | TBD | | | | | | |
| probe-subagent-inbox-metrics | TBD | | | | | | |
| probe-callback-delivery | TBD | | | | | | |
| probe-session-persistence | TBD | | | | | | |
| probe-handoff-integrity | TBD | | | | | | |
| route-rebind-guard-heartbeat | TBD | | | | | | |

---

## 7. False Capture / Duplicate Memory Signals

### Detection Method

```python
# Check for false captures
# (non-user content captured as memory)

def detect_false_captures():
    memories = query_all_memories()
    false_positives = []
    
    for mem in memories:
        # Check if content looks like wrapper
        if "<relevant-memories>" in mem.content:
            false_positives.append(mem)
        if "merged prompt" in mem.content.lower():
            false_positives.append(mem)
    
    return false_positives
```

### Metrics Table

| Metric | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 |
|--------|-------|-------|-------|-------|-------|-------|-------|
| False captures detected | 0 | | | | | | |
| Duplicate memories | 0 | | | | | | |
| Wrapper captures | 0 | | | | | | |
| Merged prompt captures | 0 | | | | | | |

### Alert Thresholds

| Signal | Threshold | Action |
|--------|-----------|--------|
| False capture | > 0 | Immediate investigation |
| Duplicate | > 5 | Check dedup logic |
| Wrapper capture | > 0 | Check source guard |

---

## Daily Collection Script

```bash
#!/bin/bash
# collect-observation-metrics.sh
# Run daily during observation window

DATE=$(date +%Y-%m-%d)
OUTPUT_DIR=~/.openclaw/workspace/artifacts/observation_metrics
mkdir -p "$OUTPUT_DIR"

# Memory metrics
~/.openclaw/workspace/tools/memory-daily-obs --json > "$OUTPUT_DIR/memory_$DATE.json"

# Policy metrics
~/.openclaw/workspace/tools/policy-daily-check --json > "$OUTPUT_DIR/policy_$DATE.json"

# Inbox metrics
~/.openclaw/workspace/tools/subagent-inbox-metrics --json > "$OUTPUT_DIR/inbox_$DATE.json"

# Continuity metrics
~/.openclaw/workspace/tools/session-continuity-daily-check --json > "$OUTPUT_DIR/continuity_$DATE.json"

# Aggregate
echo "{\"date\": \"$DATE\", \"collected\": true}" >> "$OUTPUT_DIR/summary.jsonl"

echo "Metrics collected for $DATE"
```

---

## Summary Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                   OBSERVATION WINDOW STATUS                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Memory-LanceDB   │ Row: 2 │ False: 0 │ Dup: 0 │ Status: ✅    │
│  Policy Samples   │ DENY: ? │ WARN: ? │ Eval: ? │ Status: ⏳   │
│  verify-and-close │ Calls: ? │ Block: ? │ Receipt: ? │ Status: ⏳│
│  Callback Inbox   │ Pending: ? │ Age: ? │ Stuck: ? │ Status: ⏳ │
│  Continuity       │ Recover: ? │ Handoff: ? │ WAL: ? │ Status: ⏳│
│                                                                 │
│  Observation Day: 1/7                                          │
│  Freeze Status: ACTIVE                                         │
│  End Date: ~2026-03-17                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Decision Log

### Day 1 (2026-03-10)

- **Action**: Started observation window
- **Baseline**: Gate 1.7.7 (Memory-LancedDB Source Isolation Fix)
- **Notes**: Initial metrics collected, all green

### Day N Template

- **Action**: [Describe any action taken]
- **Issues**: [Describe any issues found]
- **Resolution**: [Describe resolution if applicable]
