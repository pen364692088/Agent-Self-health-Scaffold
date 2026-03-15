# Repository Scope Definition

**Repository**: Agent-Self-health-Scaffold
**Purpose**: Self-healing execution kernel scaffold design and specifications
**Baseline Tag**: `clean-baseline-20260314`

---

## Allowed Content

### Root Level
- `README.md`, `AGENTS.md`, `BOOTSTRAP.md`, `USER.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `HEARTBEAT.md`, `memory.md`
- `.gitignore`, `pytest.ini`, `requirements.txt`, `setup.py`, `pyproject.toml`

### Allowed Directories
- `docs/` - Documentation
- `tests/` - Test files
- `tools/` - Tool scripts
- `schemas/` - JSON schemas
- `examples/` - Examples
- `agents/` - Agent configurations
- `config/` - Configuration (except runtime config)
- `memory/` - Memory files
- `scripts/` - Utility scripts

### Allowed Artifacts
- `artifacts/phase1/` - Phase 1 artifacts
- `artifacts/baseline_v2.1/` - Baseline artifacts
- `artifacts/gate1_7_*/` - Gate artifacts
- `artifacts/*.md` - Design documents

---

## Forbidden Content

### Unrelated Projects
- `OpenEmotion/`
- `OpenEmotion_MVP5/`
- Any other project directories

### Runtime Data
- `.openviking*/`
- `.openviking-data-local-ollama/`

### Runtime Modules
- `modules/` - Belongs to EgoCore

### Session/State Files
- `checkpoints/`
- `logs/`
- `*.jsonl` at root level

### Runtime Artifacts
- `artifacts/context_compression/`
- `artifacts/distilled/`
- `artifacts/integration/`
- `artifacts/openviking/`
- `artifacts/prompt_pilot/`
- `artifacts/prompt_preview/`
- `artifacts/recovery_preview/`
- `artifacts/shadow_compare/`
- `artifacts/auto_resume/`
- `artifacts/self_health/`
- `artifacts/session_reuse/`
- `artifacts/test_tmp/`
- `artifacts/materialized_state/`

### Runtime Config
- `config/prompt_pilot.json`
- `cerebras_config.json`

### Installed Skills
- `skills/` - Should be in workspace, not repo

---

## Validation

### Local Check
```bash
./scripts/check_repo_scope.sh
```

### Pre-commit Hook (recommended)
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
./scripts/check_repo_scope.sh || exit 1
```

### CI Integration
Add to `.github/workflows/ci.yml`:
```yaml
- name: Check repository scope
  run: ./scripts/check_repo_scope.sh
```

---

## Reference

Full documentation: `docs/repo-governance/CANONICAL_SCOPE.md`

---

*Baseline: clean-baseline-20260314*
