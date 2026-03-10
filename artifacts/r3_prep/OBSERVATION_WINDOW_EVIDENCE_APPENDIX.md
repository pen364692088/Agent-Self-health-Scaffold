# Observation Window Evidence Appendix

**Generated**: 2026-03-10 07:10 CST
**Version**: 1.0
**Purpose**: Collect real-world evidence during observation window to validate patch priorities

---

## Evidence Collection Strategy

### Data Sources

| Source | Collection Method | Frequency |
|--------|-------------------|-----------|
| Message logs | grep patterns | Daily |
| Policy violations | policy-violations-report | Daily |
| Receipt logs | Check receipts dir | Daily |
| Tool usage | session-query | Weekly |
| Heartbeat probes | journalctl | Daily |

---

## Evidence Category 1: Bypass Occurrences

### E1.1: Direct message tool for completion

**Question**: How often is `message` tool used directly for completion messages?

**Collection Method**:
```bash
# Count completion patterns in message logs
grep -c "任务.*完成\|已完成\|可以交付\|全部完成" logs/messages.log 2>/dev/null || echo "0"

# Count safe-message usage
grep -c "safe-message" logs/openclaw.log 2>/dev/null || echo "0"

# Compare ratios
```

**Evidence Log**:

| Date | Direct message (completion) | safe-message | Ratio |
|------|----------------------------|--------------|-------|
| Day 1 | TBD | TBD | TBD |
| Day 2 | TBD | TBD | TBD |
| Day 3 | TBD | TBD | TBD |
| Day 4 | TBD | TBD | TBD |
| Day 5 | TBD | TBD | TBD |
| Day 6 | TBD | TBD | TBD |
| Day 7 | TBD | TBD | TBD |

**Priority Adjustment**:
- If ratio > 20%: P0-1 becomes critical
- If ratio < 5%: P0-1 can be deprioritized

---

### E1.2: safe-message --force usage

**Question**: Is `--force` flag being used? How often?

**Collection Method**:
```bash
# Check for --force usage
grep -c "\\-\\-force" logs/openclaw.log 2>/dev/null || echo "0"

# Check audit log if exists
cat artifacts/audit/force_send_audit.jsonl 2>/dev/null | wc -l || echo "0"
```

**Evidence Log**:

| Date | --force attempts | Reason (if logged) |
|------|------------------|-------------------|
| Day 1 | TBD | TBD |
| Day 2 | TBD | TBD |
| Day 3 | TBD | TBD |
| Day 4 | TBD | TBD |
| Day 5 | TBD | TBD |
| Day 6 | TBD | TBD |
| Day 7 | TBD | TBD |

**Priority Adjustment**:
- If usage > 5/day: P0-3 becomes critical
- If usage = 0: P0-3 can be simplified

---

### E1.3: finalize-response without receipt

**Question**: How often is finalize-response called without verify-and-close?

**Collection Method**:
```bash
# Check finalize log for missing receipts
cat reports/finalize_log.jsonl 2>/dev/null | grep "missing_receipts" | wc -l || echo "0"

# Compare with total finalize calls
cat reports/finalize_log.jsonl 2>/dev/null | wc -l || echo "0"
```

**Evidence Log**:

| Date | finalize calls | missing receipts | Rate |
|------|----------------|------------------|------|
| Day 1 | TBD | TBD | TBD |
| Day 2 | TBD | TBD | TBD |
| Day 3 | TBD | TBD | TBD |
| Day 4 | TBD | TBD | TBD |
| Day 5 | TBD | TBD | TBD |
| Day 6 | TBD | TBD | TBD |
| Day 7 | TBD | TBD | TBD |

**Priority Adjustment**:
- If rate > 10%: P0-2 becomes critical
- If rate = 0: P0-2 can be simplified to warning only

---

## Evidence Category 2: Duplicate Path Usage

### E2.1: Memory retrieval tool usage

**Question**: Which memory retrieval tools are actually being used?

**Collection Method**:
```bash
# Count calls to each tool
for tool in session-query memory-retrieve memory-search context-retrieve; do
    count=$(grep -c "$tool" logs/openclaw.log 2>/dev/null || echo "0")
    echo "$tool: $count"
done
```

**Evidence Log**:

| Tool | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 | Total |
|------|-------|-------|-------|-------|-------|-------|-------|-------|
| session-query | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| memory-retrieve | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| memory-search | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| context-retrieve | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

**Priority Adjustment**:
- If memory-retrieve/search usage = 0: Can delete immediately
- If usage distributed: Prioritize consolidation

---

### E2.2: State writing tool usage

**Question**: Is state-write-atomic used? Does it bypass safe-write?

**Collection Method**:
```bash
# Count state-write-atomic calls
grep -c "state-write-atomic" logs/openclaw.log 2>/dev/null || echo "0"

# Count safe-write calls
grep -c "safe-write" logs/openclaw.log 2>/dev/null || echo "0"
```

**Evidence Log**:

| Date | state-write-atomic | safe-write | Total writes |
|------|-------------------|------------|--------------|
| Day 1 | TBD | TBD | TBD |
| Day 2 | TBD | TBD | TBD |
| Day 3 | TBD | TBD | TBD |
| Day 4 | TBD | TBD | TBD |
| Day 5 | TBD | TBD | TBD |
| Day 6 | TBD | TBD | TBD |
| Day 7 | TBD | TBD | TBD |

**Priority Adjustment**:
- If state-write-atomic used frequently: P1-5 becomes important
- If safe-write already dominant: P1-5 can be simplified

---

## Evidence Category 3: Legacy/Deprecated Tool Usage

### E3.1: verify-and-close-v2 usage

**Collection Method**:
```bash
grep -c "verify-and-close-v2" logs/openclaw.log 2>/dev/null || echo "0"
```

**Evidence**: TBD

**Decision**:
- If 0: Safe to delete immediately
- If > 0: Check callers and migrate

---

### E3.2: check-subagent-mailbox usage

**Collection Method**:
```bash
grep -c "check-subagent-mailbox" logs/openclaw.log 2>/dev/null || echo "0"
```

**Evidence**: TBD

**Decision**:
- If 0: Safe to delete immediately
- If > 0: Update callers to use subagent-inbox

---

### E3.3: callback-handler usage

**Collection Method**:
```bash
grep -c "callback-handler[^-]" logs/openclaw.log 2>/dev/null || echo "0"
```

**Evidence**: TBD

**Decision**:
- If 0: Safe to delete immediately
- If > 0: Update callers to use subagent-completion-handler

---

## Evidence Category 4: Policy System Health

### E4.1: Policy violation rate

**Collection Method**:
```bash
~/.openclaw/workspace/tools/policy-violations-report --today --json 2>/dev/null
```

**Evidence Log**:

| Date | DENY count | WARN count | Top violation |
|------|------------|------------|---------------|
| Day 1 | TBD | TBD | TBD |
| Day 2 | TBD | TBD | TBD |
| Day 3 | TBD | TBD | TBD |
| Day 4 | TBD | TBD | TBD |
| Day 5 | TBD | TBD | TBD |
| Day 6 | TBD | TBD | TBD |
| Day 7 | TBD | TBD | TBD |

**Sample Maturity Check**:
```bash
~/.openclaw/workspace/tools/policy-violation-summary --hours 168 --json 2>/dev/null | jq '.sample_maturity'
```

---

### E4.2: Edit tool attempts on protected paths

**Collection Method**:
```bash
# Check for edit tool violations
grep -c "OPENCLAW_PATH_NO_EDIT" logs/execution_policy_heartbeat.jsonl 2>/dev/null || echo "0"
```

**Evidence Log**:

| Date | Edit attempts on protected paths |
|------|----------------------------------|
| Day 1 | TBD |
| Day 2 | TBD |
| Day 3 | TBD |
| Day 4 | TBD |
| Day 5 | TBD |
| Day 6 | TBD |
| Day 7 | TBD |

---

## Evidence Category 5: Memory System Health

### E5.1: AutoCapture metrics

**Collection Method**:
```bash
~/.openclaw/workspace/tools/memory-daily-obs --json 2>/dev/null
```

**Evidence Log**:

| Metric | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 |
|--------|-------|-------|-------|-------|-------|-------|-------|
| Row count | 2 | TBD | TBD | TBD | TBD | TBD | TBD |
| False captures | 0 | TBD | TBD | TBD | TBD | TBD | TBD |
| Duplicate captures | 0 | TBD | TBD | TBD | TBD | TBD | TBD |
| Embedding errors | 0 | TBD | TBD | TBD | TBD | TBD | TBD |

---

### E5.2: Recall injection rate

**Collection Method**:
```bash
# Count recall injections in session
grep -c "memory_recall" logs/openclaw.log 2>/dev/null || echo "0"
```

**Evidence Log**:

| Date | Recall calls | Successful | Failed |
|------|--------------|------------|--------|
| Day 1 | TBD | TBD | TBD |
| Day 2 | TBD | TBD | TBD |
| Day 3 | TBD | TBD | TBD |
| Day 4 | TBD | TBD | TBD |
| Day 5 | TBD | TBD | TBD |
| Day 6 | TBD | TBD | TBD |
| Day 7 | TBD | TBD | TBD |

---

## Automated Evidence Collection Script

```bash
#!/bin/bash
# collect_evidence.sh - Daily evidence collection

DATE=$(date +%Y-%m-%d)
OUTPUT_DIR=~/.openclaw/workspace/artifacts/observation_evidence
mkdir -p "$OUTPUT_DIR"

echo "=== Evidence Collection: $DATE ==="

# E1: Bypass occurrences
echo "E1.1: Direct message completion patterns"
grep -c "任务.*完成\|已完成\|可以交付" logs/messages.log 2>/dev/null || echo "0"

echo "E1.2: --force usage"
grep -c "\\-\\-force" logs/openclaw.log 2>/dev/null || echo "0"

echo "E1.3: finalize without receipt"
cat reports/finalize_log.jsonl 2>/dev/null | grep "missing_receipts" | wc -l || echo "0"

# E2: Duplicate path usage
echo "E2.1: Memory tool usage"
for tool in session-query memory-retrieve memory-search context-retrieve; do
    echo "  $tool: $(grep -c $tool logs/openclaw.log 2>/dev/null || echo 0)"
done

echo "E2.2: State write usage"
echo "  state-write-atomic: $(grep -c state-write-atomic logs/openclaw.log 2>/dev/null || echo 0)"
echo "  safe-write: $(grep -c safe-write logs/openclaw.log 2>/dev/null || echo 0)"

# E3: Legacy tool usage
echo "E3: Legacy tool usage"
echo "  verify-and-close-v2: $(grep -c verify-and-close-v2 logs/openclaw.log 2>/dev/null || echo 0)"
echo "  check-subagent-mailbox: $(grep -c check-subagent-mailbox logs/openclaw.log 2>/dev/null || echo 0)"
echo "  callback-handler: $(grep -c 'callback-handler[^-]' logs/openclaw.log 2>/dev/null || echo 0)"

# E4: Policy health
echo "E4.1: Policy violations"
~/.openclaw/workspace/tools/policy-violations-report --today --summary 2>/dev/null || echo "N/A"

# E5: Memory health
echo "E5: Memory metrics"
~/.openclaw/workspace/tools/memory-daily-obs --json 2>/dev/null | jq '.' || echo "N/A"

# Save to file
echo "Evidence saved to $OUTPUT_DIR/evidence_$DATE.json"
```

---

## Evidence-Based Priority Adjustment

### Decision Matrix

| Evidence | Threshold | Priority Change |
|----------|-----------|-----------------|
| Direct message completion > 20% | HIGH | P0-1 → Critical |
| --force usage > 5/day | HIGH | P0-3 → Critical |
| finalize without receipt > 10% | HIGH | P0-2 → Critical |
| memory-retrieve/search usage = 0 | LOW | Can delete immediately |
| state-write-atomic > safe-write | MEDIUM | P1-5 → Higher priority |
| Legacy tool usage > 0 | LOW | Migrate before delete |
| False captures > 0 | CRITICAL | Extend observation |
| Policy DENY rate > 10/day | MEDIUM | Review policies |

### Post-Observation Priority Ranking

**Will be determined based on collected evidence.**

Current ranking (pre-evidence):
1. P0-1: Block direct message (Security)
2. P0-2: Receipt check (Reliability)
3. P0-3: --force audit (Security)
4. P1-4: Memory consolidation (Maintainability)
5. P1-5: State writing integration (Maintainability)

**Post-evidence ranking will be documented in PATCH_QUEUE_VERDICT.md**

---

## Daily Evidence Summary Template

```markdown
## Day N Evidence Summary (YYYY-MM-DD)

### Bypass Evidence
- Direct message completion: X occurrences
- --force usage: X occurrences
- finalize without receipt: X occurrences

### Usage Evidence
- Memory tools: session-query X, memory-retrieve X, memory-search X
- State tools: state-write-atomic X, safe-write X
- Legacy tools: v2 X, mailbox X, handler X

### Health Evidence
- Policy violations: DENY X, WARN X
- Memory: rows X, false X, dup X
- Heartbeat: ALERT X

### Priority Adjustments
- [None / Specific changes based on evidence]
```
