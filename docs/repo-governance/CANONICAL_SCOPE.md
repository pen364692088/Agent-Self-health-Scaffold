# Canonical Scope - Agent-Self-health-Scaffold

**Repository**: https://github.com/pen364692088/Agent-Self-health-Scaffold
**Purpose**: Self-healing execution kernel scaffold design and specifications
**Version**: 2026-03-14

---

## Allowed Content (Whitelist)

### Root Level Files
- `README.md` - Project readme
- `AGENTS.md` - Agent behavior specification
- `BOOTSTRAP.md` - Bootstrap documentation
- `USER.md` - User preferences
- `SOUL.md` - Core principles
- `TOOLS.md` - Tool usage guidelines
- `IDENTITY.md` - Agent identity
- `HEARTBEAT.md` - Heartbeat rules
- `memory.md` - Memory bootstrap
- `.gitignore` - Git ignore rules
- `requirements.txt` - Python dependencies
- `setup.py`, `pyproject.toml` - Python package config

### Documentation (`docs/`)
- Design documents (*.md)
- Architecture specifications
- Policy documents
- API specifications
- Runbooks

### Tests (`tests/`)
- Test files (`test_*.py`, `*_test.py`)
- Test fixtures
- Pytest configuration

### Tools (`tools/`)
- Shell scripts (*.sh)
- Python scripts (*.py)
- Executables
- **Excluded**: Runtime-specific tools that belong to EgoCore

### Schemas (`schemas/`)
- JSON schemas
- YAML schemas
- Validation schemas

### Examples (`examples/`)
- Example code
- Sample configurations
- Demonstrations

### Agents (`agents/`)
- Agent configurations
- Agent definitions

### Config (`config/`)
- Static configuration files
- **Excluded**: Runtime-specific config (e.g., `prompt_pilot.json`)

### Core Design (`core/`) - **LIMITED**
- Only design documents and interfaces
- **Excluded**: Runtime implementation code

### Artifacts (`artifacts/`) - **LIMITED**
- `artifacts/phase1/` - Phase 1 artifacts
- Design artifacts
- **Excluded**: Runtime-generated artifacts

---

## Forbidden Content (Blacklist)

### 1. Unrelated Projects
- `OpenEmotion/` - Complete unrelated project
- Any other project directories

### 2. Runtime Data
- `.openviking-data-local-ollama/` - OpenViking runtime
- `.openviking/` - OpenViking data
- Any `.*-data/` directories

### 3. Runtime Modules
- `modules/runtime_metrics_aggregator/` - Belongs to EgoCore
- `modules/emotion_context_formatter/` - Belongs to EgoCore
- Any `modules/` subdirectories

### 4. Runtime Code
- `core/canonical_adapter.py` - Runtime implementation
- `core/materialized_state_v0.py` - Runtime implementation
- `core/prompt_pilot_runner.py` - Runtime implementation
- `core/prompt_preview.py` - Runtime implementation
- `core/recovery_preview.py` - Runtime implementation
- `core/reconciler/` - Runtime implementation
- `core/state_materializer.py` - Runtime implementation
- `core/task_ledger.py` - Runtime implementation

### 5. Session/State Files
- `checkpoints/` - Session checkpoints
- `session*/` - Session directories
- `state/` - State files
- `ledger/` - Ledger files
- `heartbeat/` - Heartbeat files
- `*.jsonl` at root level (except allowed)

### 6. Runtime Artifacts
- `artifacts/context_compression/` - Runtime compression
- `artifacts/distilled/` - Distilled output
- `artifacts/integration/` - Integration artifacts
- `artifacts/prompt_pilot/` - Pilot artifacts
- `artifacts/prompt_preview/` - Preview artifacts
- `artifacts/recovery_preview/` - Recovery artifacts
- `artifacts/shadow_compare/` - Shadow comparison
- `artifacts/verification/` - Verification artifacts (except design)
- `artifacts/auto_resume/` - Auto resume logs
- `artifacts/openviking/` - OpenViking artifacts
- `artifacts/self_health/` - Self health logs
- `artifacts/memory_*/` - Memory artifacts

### 7. Runtime Config
- `config/prompt_pilot.json` - Runtime config
- `cerebras_config.json` - Secrets (should be in .gitignore)

### 8. Logs
- `logs/` - All log files

### 9. Cache
- `__pycache__/`
- `.pytest_cache/`
- `*.pyc`, `*.pyo`
- `.venv/`, `venv/`

### 10. IDE/Editor
- `.vscode/`
- `.idea/`
- `*.swp`, `*.swo`

### 11. OS Files
- `.DS_Store`
- `Thumbs.db`

---

## Boundary Rules

1. **This repository is for DESIGN and SPECIFICATIONS**
   - Not for runtime implementation
   - Not for running code
   - Not for session data

2. **Runtime implementation goes to EgoCore**
   - `/home/moonlight/Project/Github/MyProject/EgoCore`
   - https://github.com/pen364692088/EgoCore

3. **Session data stays in OpenClaw workspace**
   - `~/.openclaw/workspace/`
   - Never committed to any repo

4. **Before any commit, verify**
   - `pwd` - Correct directory?
   - `git remote -v` - Correct remote?
   - Files are in whitelist?

---

## Validation Commands

```bash
# Check for forbidden content
find . -type d -name "OpenEmotion" -o -name ".openviking*" -o -name "modules" -o -name "checkpoints"

# Check artifacts scope
ls artifacts/ | grep -v phase1

# Verify no runtime code in core/
ls core/*.py 2>/dev/null | grep -v __pycache__
```

---

*Last updated: 2026-03-14*
