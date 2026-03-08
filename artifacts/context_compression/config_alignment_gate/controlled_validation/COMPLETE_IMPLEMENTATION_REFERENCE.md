# Context Compression - Complete Implementation Reference

## Full System Implementation

### Hook Handler Complete Implementation

The hook handler is the central coordinator for all compression operations. This section provides the complete implementation reference.

#### Handler Structure

```typescript
interface CompressionConfig {
  enabled: boolean;
  mode: 'shadow' | 'light_enforced' | 'full_enforced';
  thresholds: {
    observe: number;
    candidate: number;
    enforced: number;
    strong: number;
  };
  contextWindow: number;
}

interface CompressionResult {
  triggered: boolean;
  event_id?: string;
  capsules_created?: number;
  post_ratio?: number;
  duration_ms?: number;
}

interface CounterState {
  enforced_sessions_total: number;
  enforced_low_risk_sessions: number;
  bypass_sessions_total: number;
  sessions_skipped_by_scope_filter: number;
  budget_check_call_count: number;
  sessions_evaluated_by_budget_check: number;
  sessions_over_threshold: number;
  compression_opportunity_count: number;
  enforced_trigger_count: number;
  retrieve_call_count: number;
  real_reply_corruption_count: number;
  active_session_pollution_count: number;
  rollback_event_count: number;
  hook_error_count: number;
  kill_switch_triggers: number;
}
```

#### Main Handler Function

```typescript
async function handler(event: Event): Promise<void> {
  // Step 1: Validate event
  if (!isValidEvent(event)) {
    return;
  }

  const sessionKey = event.sessionKey || 'unknown';
  const counters = readCounters();
  const config = loadConfig();

  try {
    // Step 2: Check feature flags
    if (!config.enabled) {
      incrementCounter(counters, 'bypass_sessions_total');
      writeCounters(counters);
      return;
    }

    // Step 3: Check kill switch
    if (isKillSwitchActive()) {
      incrementCounter(counters, 'kill_switch_triggers');
      logRollback('kill_switch_active', sessionKey);
      writeCounters(counters);
      return;
    }

    // Step 4: Classify session
    const sessionType = classifySession(event);
    if (!isSessionEligible(sessionType)) {
      incrementCounter(counters, 'sessions_skipped_by_scope_filter');
      writeCounters(counters);
      return;
    }

    // Step 5: Run budget check
    incrementCounter(counters, 'budget_check_call_count');
    const budgetResult = await runBudgetCheck(sessionKey, config.contextWindow);
    incrementCounter(counters, 'sessions_evaluated_by_budget_check');

    if (!budgetResult) {
      incrementCounter(counters, 'hook_error_count');
      writeCounters(counters);
      return;
    }

    // Step 6: Check thresholds
    if (shouldCompress(budgetResult, config)) {
      incrementCounter(counters, 'sessions_over_threshold');
      incrementCounter(counters, 'compression_opportunity_count');

      // Step 7: Execute compression
      const result = await executeCompression(
        sessionKey,
        config.mode,
        budgetResult
      );

      if (result.triggered) {
        incrementCounter(counters, 'enforced_trigger_count');
        
        // Step 8: Run retrieval
        await runRetrieval(sessionKey);
        incrementCounter(counters, 'retrieve_call_count');
      } else {
        incrementCounter(counters, 'rollback_event_count');
        logRollback('compression_failed', sessionKey);
      }
    }

    writeCounters(counters);
  } catch (error) {
    console.error('[compression] Handler error:', error);
    incrementCounter(counters, 'hook_error_count');
    writeCounters(counters);
  }
}
```

#### Budget Check Implementation

```typescript
async function runBudgetCheck(
  sessionKey: string,
  maxTokens: number
): Promise<BudgetResult | null> {
  const historyPath = findSessionFile(sessionKey);
  if (!historyPath) {
    return null;
  }

  const toolPath = join(WORKSPACE, 'tools', 'context-budget-check');
  const result = await runTool(toolPath, [
    '--history', historyPath,
    '--max-tokens', String(maxTokens),
    '--json'
  ]);

  if (result.exitCode !== 0) {
    console.error('[compression] Budget check failed:', result.stderr);
    return null;
  }

  try {
    const data = JSON.parse(result.stdout);
    const ratio = data.ratio || 0;
    
    return {
      estimated_tokens: data.estimated_tokens || 0,
      max_tokens: maxTokens,
      ratio: ratio,
      pressure_level: data.pressure_level || 'normal',
      threshold_hit: data.threshold_hit,
      should_compress: ratio >= 0.85
    };
  } catch (error) {
    console.error('[compression] Failed to parse budget check:', error);
    return null;
  }
}
```

#### Compression Execution

```typescript
async function executeCompression(
  sessionKey: string,
  mode: string,
  budget: BudgetResult
): Promise<CompressionResult> {
  const historyPath = findSessionFile(sessionKey);
  const statePath = join(WORKSPACE, 'state', 'active_state.json');
  
  if (!historyPath) {
    return { triggered: false };
  }

  const toolPath = join(WORKSPACE, 'tools', 'context-compress');
  const result = await runTool(toolPath, [
    '--session-id', sessionKey,
    '--state', statePath,
    '--history', historyPath,
    '--max-tokens', String(budget.max_tokens),
    '--mode', mode,
    '--json'
  ]);

  if (result.exitCode !== 0) {
    console.error('[compression] Compression failed:', result.stderr);
    return { triggered: false };
  }

  try {
    const data = JSON.parse(result.stdout);
    return {
      triggered: data.compression_triggered || false,
      event_id: data.event_id,
      capsules_created: data.capsules?.length || 0,
      post_ratio: data.after?.ratio,
      duration_ms: data.duration_ms
    };
  } catch (error) {
    console.error('[compression] Failed to parse result:', error);
    return { triggered: false };
  }
}
```

---

## State Machine Complete Implementation

### State Definitions

```typescript
enum CompressionState {
  IDLE = 'idle',
  CANDIDATE = 'candidate',
  PENDING = 'pending',
  EXECUTING = 'executing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  ROLLBACK = 'rollback'
}

interface StateTransition {
  from: CompressionState;
  to: CompressionState;
  condition: (budget: BudgetResult) => boolean;
  action: () => void;
}
```

### Transition Table

```typescript
const transitions: StateTransition[] = [
  {
    from: CompressionState.IDLE,
    to: CompressionState.CANDIDATE,
    condition: (budget) => budget.ratio >= 0.75,
    action: () => console.log('[state] idle → candidate')
  },
  {
    from: CompressionState.CANDIDATE,
    to: CompressionState.PENDING,
    condition: (budget) => budget.ratio >= 0.85,
    action: () => console.log('[state] candidate → pending')
  },
  {
    from: CompressionState.PENDING,
    to: CompressionState.EXECUTING,
    condition: () => true, // Always execute from pending
    action: () => console.log('[state] pending → executing')
  },
  {
    from: CompressionState.EXECUTING,
    to: CompressionState.COMPLETED,
    condition: () => compressionSuccess,
    action: () => console.log('[state] executing → completed')
  },
  {
    from: CompressionState.EXECUTING,
    to: CompressionState.FAILED,
    condition: () => compressionFailed,
    action: () => console.log('[state] executing → failed')
  },
  {
    from: CompressionState.FAILED,
    to: CompressionState.ROLLBACK,
    condition: () => true,
    action: () => console.log('[state] failed → rollback')
  },
  {
    from: CompressionState.ROLLBACK,
    to: CompressionState.IDLE,
    condition: () => rollbackComplete,
    action: () => console.log('[state] rollback → idle')
  },
  {
    from: CompressionState.COMPLETED,
    to: CompressionState.IDLE,
    condition: (budget) => budget.ratio < 0.75,
    action: () => console.log('[state] completed → idle')
  }
];
```

### State Machine Class

```typescript
class CompressionStateMachine {
  private state: CompressionState = CompressionState.IDLE;
  private transitions: StateTransition[];

  constructor(transitions: StateTransition[]) {
    this.transitions = transitions;
  }

  getState(): CompressionState {
    return this.state;
  }

  transition(budget: BudgetResult): boolean {
    for (const transition of this.transitions) {
      if (transition.from === this.state && transition.condition(budget)) {
        console.log(`[state-machine] ${transition.from} → ${transition.to}`);
        this.state = transition.to;
        transition.action();
        return true;
      }
    }
    return false;
  }

  canTransition(budget: BudgetResult): boolean {
    for (const transition of this.transitions) {
      if (transition.from === this.state && transition.condition(budget)) {
        return true;
      }
    }
    return false;
  }
}
```

---

## Evidence Collector Complete Implementation

### Evidence Collection Manager

```typescript
class EvidenceCollector {
  private evidenceDir: Path;
  private sessionId: string;

  constructor(sessionId: string, evidenceDir: Path) {
    this.sessionId = sessionId;
    this.evidenceDir = evidenceDir;
    ensureDir(evidenceDir);
  }

  async captureCounterBefore(counters: CounterState): Promise<Path> {
    const path = this.evidenceDir.join('counter_before.json');
    const content = {
      timestamp: new Date().toISOString(),
      session_id: this.sessionId,
      enforced_counters: counters
    };
    await writeFile(path, JSON.stringify(content, null, 2));
    return path;
  }

  async captureCounterAfter(counters: CounterState): Promise<Path> {
    const path = this.evidenceDir.join('counter_after.json');
    const content = {
      timestamp: new Date().toISOString(),
      session_id: this.sessionId,
      enforced_counters: counters
    };
    await writeFile(path, JSON.stringify(content, null, 2));
    return path;
  }

  async captureBudgetBefore(budget: BudgetResult): Promise<Path> {
    const path = this.evidenceDir.join('budget_before.json');
    const content = {
      timestamp: new Date().toISOString(),
      session_id: this.sessionId,
      ...budget
    };
    await writeFile(path, JSON.stringify(content, null, 2));
    return path;
  }

  async captureBudgetAfter(budget: BudgetResult): Promise<Path> {
    const path = this.evidenceDir.join('budget_after.json');
    const content = {
      timestamp: new Date().toISOString(),
      session_id: this.sessionId,
      ...budget
    };
    await writeFile(path, JSON.stringify(content, null, 2));
    return path;
  }

  async captureGuardrailEvent(event: GuardrailEvent): Promise<Path> {
    const path = this.evidenceDir.join('guardrail_event.json');
    const content = {
      ...event,
      session_id: this.sessionId,
      timestamp: new Date().toISOString()
    };
    await writeFile(path, JSON.stringify(content, null, 2));
    return path;
  }

  async captureCapsuleMetadata(capsule: Capsule): Promise<Path> {
    const path = this.evidenceDir.join('capsule_metadata.json');
    await writeFile(path, JSON.stringify(capsule, null, 2));
    return path;
  }

  async validatePackage(): Promise<{ valid: boolean; errors: string[] }> {
    const errors: string[] = [];
    
    const requiredFiles = [
      'counter_before.json',
      'counter_after.json',
      'budget_before.json',
      'budget_after.json',
      'guardrail_event.json',
      'capsule_metadata.json'
    ];

    for (const file of requiredFiles) {
      if (!this.evidenceDir.join(file).exists()) {
        errors.push(`Missing: ${file}`);
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:17:00-06:00
**Purpose**: Complete Implementation Reference
