# Checkpointed Step Loop v2 - Execution Contract

## Overview

This document defines the execution layer for Checkpointed Step Loop v2, connecting step packets to real execution backends (shell, python, file mutation).

## Core Principle

**Execution truth is machine-verifiable; handoff is human-readable summary.**

The execution layer must produce structured receipts that can be validated without reading the original conversation.

---

## Step Types

### Supported Types

| Type | Description | Inputs | Outputs |
|------|-------------|--------|---------|
| `analyze` | Read/analyze files or data | file paths, queries | analysis result |
| `execute_shell` | Run shell command | command, cwd, env | exit_code, stdout, stderr |
| `execute_python` | Run Python script | script, args | return value, stdout |
| `modify_files` | Create/modify/delete files | file specs | changed files |
| `run_tests` | Execute test suite | test paths, args | test results |
| `verify_outputs` | Verify expected outputs | expected files, validators | verification result |

### Step Packet Extension

```json
{
  "step_id": "S01",
  "step_type": "execute_shell",
  "title": "Run build",
  "goal": "Build the project",
  "execution": {
    "command": "npm run build",
    "cwd": "/path/to/project",
    "env": {},
    "timeout_seconds": 300
  },
  "expected_outputs": [...],
  "exit_criteria": [...]
}
```

---

## Executor Interface

```python
class StepExecutor:
    """Base interface for step execution"""
    
    def prepare_execution(self, step_packet: dict, resume_context: dict) -> dict:
        """Prepare execution context"""
        pass
    
    def execute_step(self, step_packet: dict) -> ExecutionResult:
        """Execute the step and return result"""
        pass
    
    def collect_evidence(self, step_packet: dict, result: ExecutionResult) -> dict:
        """Collect execution evidence"""
        pass
    
    def classify_failure(self, result: ExecutionResult) -> str:
        """Classify failure type: retryable, blocked, fatal"""
        pass
```

---

## Execution Result

```python
@dataclass
class ExecutionResult:
    step_id: str
    status: str  # success, failed, blocked, retryable
    started_at: str
    completed_at: str
    
    # Execution receipt
    command: Optional[str]
    exit_code: Optional[int]
    stdout_path: Optional[str]
    stderr_path: Optional[str]
    
    # File changes
    changed_files: List[dict]
    generated_files: List[str]
    
    # Outputs
    outputs: dict
    
    # Failure classification
    error_type: Optional[str]
    error_message: Optional[str]
    retryable: bool
```

---

## Execution Receipt Schema

Every real step execution must produce a receipt:

```json
{
  "step_id": "S01",
  "execution_type": "execute_shell",
  "status": "success",
  "started_at": "2026-03-15T13:00:00Z",
  "completed_at": "2026-03-15T13:00:05Z",
  "duration_ms": 5000,
  
  "command": "npm run build",
  "exit_code": 0,
  "stdout_path": "evidence/S01/stdout.txt",
  "stderr_path": "evidence/S01/stderr.txt",
  
  "changed_files": [
    {"path": "dist/bundle.js", "action": "created", "lines_added": 100}
  ],
  "generated_files": ["dist/bundle.js"],
  
  "outputs": {
    "build_success": true,
    "bundle_size": "500KB"
  },
  
  "error": null,
  "retryable": false,
  
  "checksum": "sha256:..."
}
```

---

## Evidence Collection

### Automatic Evidence

For every execution, collect:

1. **stdout.txt** - Standard output
2. **stderr.txt** - Standard error
3. **exit_code.txt** - Exit code
4. **timing.json** - Start/end timestamps
5. **changed_files.json** - File modifications

### File Change Tracking

```python
def track_file_changes(before_snapshot: dict, after_snapshot: dict) -> list:
    """Compare file states and return changes"""
    changes = []
    
    for path, hash in after_snapshot.items():
        if path not in before_snapshot:
            changes.append({"path": path, "action": "created"})
        elif hash != before_snapshot[path]:
            changes.append({"path": path, "action": "modified"})
    
    for path in before_snapshot:
        if path not in after_snapshot:
            changes.append({"path": path, "action": "deleted"})
    
    return changes
```

---

## Failure Classification

| Type | Condition | Action |
|------|-----------|--------|
| `retryable` | Transient error (network, timeout) | Retry with backoff |
| `blocked` | Missing dependency, permission denied | Wait for resolution |
| `fatal` | Logic error, invalid input | Abort task |

```python
def classify_failure(exit_code: int, stderr: str) -> str:
    if exit_code in [137, 143]:  # SIGKILL, SIGTERM
        return "retryable"
    if "permission denied" in stderr.lower():
        return "blocked"
    if "not found" in stderr.lower():
        return "fatal"
    return "retryable"
```

---

## Resume-to-Execution Bridge

### Flow

```
ResumeEngine.analyze()
    ↓
ResumeContext.recovery_action
    ↓
if action == "continue" or "retry":
    ResumeExecuteBridge.bridge_to_executor()
        ↓
    StepExecutor.execute_step()
        ↓
    collect_evidence()
        ↓
    update_task_state()
```

### Bridge Logic

```python
class ResumeExecuteBridge:
    def bridge_to_executor(self, context: ResumeContext, executor: StepExecutor):
        step_id = context.current_step_id
        
        # Check lease
        if not context.lease_valid:
            # Reclaim lease
            self.lease_manager.acquire(step_id, self.worker_id)
        
        # Load step packet
        step_packet = self.dossier.get_step_packet(step_id)
        
        # Execute
        result = executor.execute_step(step_packet)
        
        # Collect evidence
        evidence = executor.collect_evidence(step_packet, result)
        
        # Save results
        self.dossier.save_step_result(step_id, result.to_dict())
        self.save_evidence(step_id, evidence)
        self.dossier.save_handoff(step_id, self.generate_handoff(result))
        
        # Update state
        self.dossier.update_step(step_id, result.status)
```

---

## Gate Integration

### Gate C Enhancement

```python
def run_gate_c(self) -> GateResult:
    # ... existing checks ...
    
    # NEW: Check execution receipts
    for step in task_state.steps:
        if step["status"] == "success":
            receipt = self.load_execution_receipt(step["step_id"])
            if not receipt:
                result.errors.append(f"Missing execution receipt for {step['step_id']}")
            elif not self.validate_receipt(receipt):
                result.errors.append(f"Invalid receipt for {step['step_id']}")
    
    # NEW: Check evidence completeness
    for step in task_state.steps:
        if step["status"] == "success":
            required_evidence = ["stdout.txt", "exit_code.txt", "timing.json"]
            for ev in required_evidence:
                if not self.evidence_exists(step["step_id"], ev):
                    result.errors.append(f"Missing {ev} for {step['step_id']}")
```

---

## Pilot Task Requirements

### Selection Criteria

1. **Low risk** - No production data modification
2. **Verifiable** - Clear success criteria
3. **Reversible** - Can be rolled back
4. **Multi-step** - At least 4 steps: analyze → execute → verify → closeout

### Recommended Pilots

1. **Documentation Index Generator**
   - Scan docs/ directory
   - Generate index markdown
   - Verify output exists
   - Closeout with summary

2. **Test Runner with Report**
   - Find test files
   - Run tests
   - Generate report
   - Archive results

3. **File Organization Task**
   - Analyze file structure
   - Reorganize files
   - Verify structure
   - Generate summary

---

## Non-Goals for v2

These are explicitly out of scope:

- Multi-worker concurrent execution
- Cross-repository task dependencies
- Notification/UI integration
- Long-running cron scheduling
- Complex failure policy extensions
- Intelligent planning enhancement

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.0 | 2026-03-15 | Initial execution contract design |
