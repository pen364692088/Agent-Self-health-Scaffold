# Phase C Controlled Validation - Full Technical Reference

## Part 1: Compression Algorithm Details

### 1.1 Token Estimation Algorithm

The token estimation algorithm uses a simple but effective heuristic:

```python
def estimate_tokens(text: str) -> int:
    """
    Estimate token count using simple heuristic: 4 chars ≈ 1 token.
    This is a rough approximation that works for most LLM tokenizers.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)
```

For JSONL files, the algorithm iterates through each line:

```python
def estimate_jsonl_tokens(path: Path) -> int:
    """Estimate tokens from JSONL file."""
    total = 0
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    if data.get('type') == 'message':
                        msg = data.get('message', {})
                        content = msg.get('content', [])
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict):
                                    total += estimate_tokens(item.get('text', ''))
                except json.JSONDecodeError:
                    total += estimate_tokens(line)
    return total
```

### 1.2 Pressure Level Calculation

Pressure levels are determined by the budget ratio:

```python
def get_pressure_level(ratio: float) -> str:
    """
    Determine pressure level based on ratio.
    
    Thresholds:
    - ratio < 0.70 → "normal"
    - ratio >= 0.70 → "light"
    - ratio >= 0.85 → "standard"
    - ratio >= 0.92 → "strong"
    """
    if ratio >= 0.92:
        return "strong"
    elif ratio >= 0.85:
        return "standard"
    elif ratio >= 0.70:
        return "light"
    else:
        return "normal"
```

### 1.3 Eviction Planning Algorithm

The eviction planning algorithm determines which turns to remove:

```python
def determine_eviction_plan(
    turn_count: int,
    pressure_level: str,
    state: Optional[Dict]
) -> Dict:
    """
    Determine which turns to evict based on pressure level.
    """
    MIN_PRESERVE_TURNS = 5
    MAX_EVICT_RATIO = 0.6
    
    if turn_count <= MIN_PRESERVE_TURNS:
        return {
            "evict_turns": [],
            "preserve_turns": list(range(1, turn_count + 1)),
            "preserve_resident": ["task_goal", "open_loops", "hard_constraints"]
        }
    
    # Calculate eviction ratio based on pressure
    if pressure_level == "strong":
        evict_ratio = 0.5
    elif pressure_level == "standard":
        evict_ratio = 0.4
    elif pressure_level == "light":
        evict_ratio = 0.25
    else:
        evict_ratio = 0
    
    evict_count = min(
        int(turn_count * evict_ratio),
        int(turn_count * MAX_EVICT_RATIO),
        turn_count - MIN_PRESERVE_TURNS
    )
    
    # Evict from the beginning, preserve recent turns
    evict_turns = list(range(1, evict_count + 1))
    preserve_turns = list(range(evict_count + 1, turn_count + 1))
    
    return {
        "evict_turns": evict_turns,
        "preserve_turns": preserve_turns,
        "preserve_resident": ["task_goal", "open_loops", "hard_constraints"]
    }
```

## Part 2: Hook Handler Implementation

### 2.1 Main Handler Flow

```typescript
const handler = async (event: any) => {
  // Only handle preprocessed messages
  if (event.type !== 'message' || event.action !== 'preprocessed') {
    return;
  }

  const counters = readCounters();
  const mode = getCompressionMode();

  try {
    // Check feature flags
    if (!isFeatureEnabled()) {
      incrementCounter(counters, 'bypass_sessions_total');
      writeCounters(counters);
      return;
    }

    // Check kill switch
    if (isKillSwitchTriggered()) {
      incrementCounter(counters, 'kill_switch_triggers');
      logRollback('kill_switch_triggered', event.sessionKey || 'unknown');
      writeCounters(counters);
      return;
    }

    // Classify session
    const sessionType = classifySession(event);
    const sessionKey = event.sessionKey || 'unknown';

    // Check if session is eligible
    if (!isSessionEligible(sessionType)) {
      incrementCounter(counters, 'sessions_skipped_by_scope_filter');
      writeCounters(counters);
      return;
    }

    // Step 1: Budget check
    incrementCounter(counters, 'budget_check_call_count');
    const budgetResult = await runBudgetCheck(sessionKey);
    incrementCounter(counters, 'sessions_evaluated_by_budget_check');

    if (!budgetResult) {
      incrementCounter(counters, 'hook_error_count');
      writeCounters(counters);
      return;
    }

    // Step 2: Check threshold
    if (budgetResult.should_compress || budgetResult.pressure_level === 'strong' || 
        budgetResult.pressure_level === 'standard' || budgetResult.pressure_level === 'light') {
      
      incrementCounter(counters, 'sessions_over_threshold');
      incrementCounter(counters, 'compression_opportunity_count');

      // Get session file paths for compression
      const historyPath = findRecentSessionFile(sessionKey);
      const statePath = join(WORKSPACE, 'state', 'active_state.json');
      
      // Step 3: Run compression based on mode
      if (mode === 'light_enforced') {
        incrementCounter(counters, 'enforced_low_risk_sessions');
        
        const compressSuccess = await runCompress(sessionKey, 'light_enforced', statePath, historyPath);
        if (compressSuccess) {
          incrementCounter(counters, 'enforced_trigger_count');
          
          // Step 4: Retrieve
          const retrieveSuccess = await runRetrieve(sessionKey);
          if (retrieveSuccess) {
            incrementCounter(counters, 'retrieve_call_count');
          }
        } else {
          incrementCounter(counters, 'rollback_event_count');
          logRollback('compress_failed', sessionKey, { mode: 'light_enforced' });
        }
      }
    }

    writeCounters(counters);
  } catch (error) {
    console.error('[context-compression] Hook error:', error);
    incrementCounter(counters, 'hook_error_count');
    writeCounters(counters);
  }
};
```

### 2.2 Budget Check Integration

```typescript
async function runBudgetCheck(sessionKey: string): Promise<any | null> {
  const toolPath = join(WORKSPACE, 'tools', 'context-budget-check');
  const sessionFile = findRecentSessionFile(sessionKey);
  
  if (sessionFile) {
    // Use runtime context window (200k) instead of hardcoded 100k
    const maxTokens = 200000;
    
    const result = await runTool(toolPath, [
      '--history', sessionFile,
      '--max-tokens', String(maxTokens)
    ]);

    if (result.exitCode !== 0) {
      console.error('[context-compression] Budget check failed:', result.stderr);
      return null;
    }

    try {
      const data = JSON.parse(result.stdout);
      const ratio = data.ratio || 0;
      
      // Threshold enforcement: 0.85 = standard, must compress
      const should_compress = ratio >= 0.85;
      
      return {
        pressure_level: data.pressure_level || 'normal',
        total_tokens: data.estimated_tokens || 0,
        max_tokens: maxTokens,
        ratio: ratio,
        should_compress: should_compress,
        threshold_hit: data.threshold_hit
      };
    } catch (error) {
      console.error('[context-compression] Failed to parse budget check result:', error);
      return null;
    }
  }
  
  return null;
}
```

## Part 3: Validation Criteria

### 3.1 Phase C Pass Conditions

Phase C is marked as PASS only when ALL conditions are satisfied:

| Condition | Requirement |
|-----------|-------------|
| Trigger Point | budget_ratio >= 0.85 |
| Timing | Before prompt assembly |
| Action | forced_standard_compression |
| Execution | runCompress succeeds |
| State Flow | compression_state transitions complete |
| Safety | real_reply_corruption_count = 0 |
| Safety | active_session_pollution_count = 0 |
| Evidence | All required files present |

### 3.2 Evidence Package Requirements

| File | Purpose |
|------|---------|
| counter_before.json | Baseline counter state |
| counter_after.json | Post-trigger counter state |
| budget_before.json | Pre-compression budget snapshot |
| budget_after.json | Post-compression budget snapshot |
| guardrail_event.json | Guardrail activation record |
| capsule_metadata.json | Capsule content and structure |
| CONTROLLED_TRIGGER_AT_085_REPORT.md | Final validation report |

### 3.3 Four Core Questions

The validation must answer these questions:

1. **trigger_ratio**: What was the ratio when compression triggered?
   - Expected: >= 0.85
   - Source: budget trace

2. **pre_assemble_compliant**: Did compression happen before assembly?
   - Expected: yes
   - Source: event timing analysis

3. **post_compression_ratio**: What was the ratio after compression?
   - Expected: < 0.75 (safe zone)
   - Source: budget_after.json

4. **safety_counters_remained_zero**: Were safety counters preserved?
   - Expected: yes
   - Source: counter comparison

## Part 4: Rollout Phases

### 4.1 Phase Progression

```
Phase A: Config Alignment Gate ✅ PASSED
    ↓
Phase B: Runtime Policy Implementation ✅ DONE
    ↓
Phase C: Controlled Validation ⏳ IN PROGRESS
    ↓
Phase D: Natural Validation ⏳ PENDING
    ↓
Phase E: Default Rollout ⏳ PENDING
```

### 4.2 Gate Conditions

**Gate A → B**:
- [x] runtime_compression_policy.json created
- [x] threshold_enforced = 0.85
- [x] max_tokens = 200000

**Gate B → C**:
- [x] Hook handler modified
- [x] runCompress parameters fixed
- [x] All tools pass self-test

**Gate C → D**:
- [ ] Controlled trigger at 0.85 captured
- [ ] pre_assemble_compliant = yes
- [ ] Safety counters = 0
- [ ] Evidence package complete

**Gate D → E**:
- [ ] Natural triggers observed
- [ ] Timing analysis complete
- [ ] No user-visible disruption

## Part 5: Technical Details

### 5.1 File Paths

```
~/.openclaw/
├── agents/main/sessions/          # Session JSONL files
├── workspace/
│   ├── state/active_state.json    # Current session state
│   ├── tools/
│   │   ├── context-budget-check   # Budget estimation tool
│   │   ├── context-compress       # Compression executor
│   │   ├── prompt-assemble        # Prompt assembly tool
│   │   └── context-retrieve       # Retrieval tool
│   └── artifacts/
│       └── context_compression/
│           ├── config_alignment_gate/
│           │   ├── runtime_compression_policy.json
│           │   ├── controlled_validation/
│           │   │   ├── CONTROLLED_TRIGGER_RUNTIME_SNAPSHOT.json
│           │   │   ├── controlled_trigger_plan.json
│           │   │   ├── controlled_budget_trace.jsonl
│           │   │   └── controlled_trigger_trace.jsonl
│           └── light_enforced/
│               └── light_enforced_counters.json
└── hooks/context-compression-shadow/
    └── handler.ts                  # Compression hook
```

### 5.2 Environment Variables

```bash
CONTEXT_COMPRESSION_ENABLED=1
CONTEXT_COMPRESSION_MODE=light_enforced
OPENCLAW_WORKSPACE=/home/moonlight/.openclaw/workspace
```

### 5.3 Configuration Files

**runtime_compression_policy.json**:
```json
{
  "policy_version": "1.0",
  "context_window": 200000,
  "thresholds": {
    "observe": 0.75,
    "candidate": 0.75,
    "enforced": 0.85,
    "strong": 0.92
  },
  "critical_rule": "不允许跨过 0.85 后继续拖延"
}
```

**light_enforced_counters.json**:
```json
{
  "status": "active",
  "mode": "light_enforced",
  "enforced_counters": {
    "enforced_sessions_total": 0,
    "enforced_trigger_count": 0,
    "real_reply_corruption_count": 0,
    "active_session_pollution_count": 0
  }
}
```

## Part 6: Monitoring and Observability

### 6.1 Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| enforced_trigger_count | Successful compressions | N/A |
| rollback_event_count | Failed compressions | > 5 |
| real_reply_corruption_count | Safety violations | > 0 |
| active_session_pollution_count | Context pollution | > 0 |

### 6.2 Health Check Endpoints

```bash
# Check compression tool health
context-compress --health

# Check budget tool health
context-budget-check --health

# Check prompt assembly health
prompt-assemble --health

# View current counters
cat light_enforced_counters.json | jq '.enforced_counters'
```

### 6.3 Event Logging

All compression events are logged to:
- `artifacts/compression_events/events.jsonl`

Event schema:
```json
{
  "event_id": "cmp_TIMESTAMP",
  "session_id": "session_001",
  "trigger": "threshold_85",
  "pressure_level": "standard",
  "before": {"tokens": 170000, "turns": 80, "ratio": 0.85},
  "after": {"tokens": 110000, "turns": 40, "ratio": 0.55},
  "mode": "enforced"
}
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T01:55:00-06:00
**Purpose**: Phase C Controlled Validation Technical Reference
