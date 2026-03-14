# Agent-Self-health-Scaffold v2

A constrained self-healing execution kernel scaffold for OpenClaw.

## Why this exists
The problem is not lack of monitoring. The problem is that after restart, corruption, or partial failure, the system often cannot continue the task automatically.

This project focuses on five primary execution-chain goals:
1. durable task truth via a ledger
2. restart-time automatic recovery
3. out-of-band restart execution
4. transcript rebuild from execution truth
5. durable parent/child subtask orchestration

---

## Current Status

**Phase 2.9: Prompt Limited Pilot Ready**

| Component | Status | Mode |
|-----------|--------|------|
| MaterializedState v0 | ✅ Complete | Frozen |
| CanonicalAdapter | ✅ Complete | Shadow only |
| PromptPreview | ✅ Complete | Shadow only |
| RecoveryPreview | ✅ Complete | Shadow only |
| Prompt Pilot | ✅ Ready | Dual gate |
| Recovery Live | ❌ Not allowed | Explicitly forbidden |
| Phase 3 | ❌ Not started | Pending decision |

### Authority Chain
**ALL prompt and recovery decisions go through `main_chain`.**

Shadow systems (MaterializedState, PromptPreview, RecoveryPreview) are read-only observers and NEVER replace main_chain authority.

### Prompt Status
- **Mode**: DISABLED (ready to start shadow)
- **Gate**: Dual gate mechanism (20 samples + 7 days)
- **Scope**: Limited to recovery_success, task_ready_to_close, gate_completed

### Recovery Status
- **Mode**: SHADOW ONLY (never live)
- **Authority**: main_chain (always)

---

## Key Documents

| Document | Purpose |
|----------|---------|
| [CURRENT_STATUS.md](CURRENT_STATUS.md) | Single source of truth for current state |
| [PHASE_2_9_DESIGN.md](PHASE_2_9_DESIGN.md) | Dual gate pilot design |
| [docs/PROMPT_PILOT_RUNBOOK.md](docs/PROMPT_PILOT_RUNBOOK.md) | Operations runbook |
| [docs/MATERIALIZED_STATE_V0_SCOPE.md](docs/MATERIALIZED_STATE_V0_SCOPE.md) | MaterializedState scope (frozen) |
| [config/prompt_pilot.json](config/prompt_pilot.json) | Pilot configuration |

---

## Quick Start

### Check Current Status
```bash
# View current pilot status
tools/prompt-pilot-control --status

# Check gate progress
tools/prompt-pilot-control --check-gate
```

### Start Shadow Mode (when ready)
```bash
# Pre-flight checks
tools/prompt-pilot-preflight

# Enable shadow mode
tools/prompt-pilot-control --enable --mode shadow
```

### Materialize State
```bash
# Basic usage
tools/materialize-state --json

# Shadow compare with canonical
tools/materialize-state --shadow-compare

# Prompt preview (shadow mode)
tools/materialize-state --prompt-preview

# Recovery preview (shadow mode)
tools/materialize-state --recovery-preview
```

---

## Test Suite

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/core/test_materialized_state_v0.py -v
pytest tests/core/test_canonical_adapter.py -v
pytest tests/core/test_prompt_preview.py -v
pytest tests/core/test_recovery_preview.py -v
pytest tests/test_phase_2_9_validation.py -v
```

**Total: 123 tests passing**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      main_chain (Authority)                  │
│                    All decisions go here                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Shadow Systems (Read-Only)                 │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ MaterializedState│  │ CanonicalAdapter │                 │
│  │      (v0)        │  │   (Shadow Only)  │                 │
│  └──────────────────┘  └──────────────────┘                 │
│           │                    │                            │
│           ▼                    ▼                            │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  PromptPreview   │  │ RecoveryPreview  │                 │
│  │  (Shadow Only)   │  │  (Shadow Only)   │                 │
│  └──────────────────┘  └──────────────────┘                 │
│           │                    │                            │
│           ▼                    ▼                            │
│  ┌─────────────────────────────────────────┐                │
│  │           Prompt Pilot                   │                │
│  │    (Dual Gate: samples + time)          │                │
│  │    Scope: recovery_success, etc.        │                │
│  └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## Constraints

| Constraint | Enforcement |
|------------|-------------|
| main_chain is authority | All decisions go through main_chain |
| No recovery live | RecoveryPreview is shadow only, never live |
| No handoff/capsule input | Not in scope for Phase 2 |
| No second live state | Shadow systems are read-only |
| Dual gate mechanism | Sample count + time, not time alone |

---

## Directory Structure

```
├── core/                    # Core execution modules
│   ├── materialized_state_v0.py
│   ├── canonical_adapter.py
│   ├── prompt_preview.py
│   ├── recovery_preview.py
│   └── prompt_pilot_runner.py
├── config/                  # Configuration files
│   └── prompt_pilot.json
├── tools/                   # CLI tools
│   ├── materialize-state
│   ├── prompt-pilot-control
│   └── prompt-pilot-preflight
├── tests/                   # Test suite (123 tests)
├── docs/                    # Documentation
├── schemas/                 # JSON schemas
├── artifacts/               # Runtime artifacts
└── state/                   # State files
```

---

## Key Rule
Task truth is primary; transcript is derived.
