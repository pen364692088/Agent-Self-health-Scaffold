# SHOULD_KEEP_TRACKED.md

**Generated**: 2026-03-13
**Repository**: Agent-Self-health-Scaffold

## Categories to Keep Tracked

### 1. Core Source Code
All `.py` files in:
- `core/` - Core reconciliation and state management
- `openviking/` - Memory indexing and retrieval system
- `runtime/` - Job orchestrators, recovery, transcript rebuilders
- `tools/` - CLI tools and scripts (excluding .bak files)
- `tests/` - Test suites
- `schemas/` - JSON schemas for validation

### 2. Configuration Templates
- `config/*.json` - Action policy, mcporter config
- `config/*.yaml` - OpenViking policies
- `*.template` files - Template versions of config files
- `.github/workflows/*.yml` - CI/CD workflows

### 3. Documentation
- `docs/**/*.md` - All documentation
- `README.md`, `AGENTS.md`, `SOUL.md`, `USER.md`
- `POLICIES/` - Policy documents
- `memory/shared/` - Shared knowledge base

### 4. Project Structure Files
- `Makefile`, `pytest.ini`, `package.json`
- `.gitignore` (updated)
- `templates/` - Workflow templates

### 5. Skills (Published/Reusable)
- `skills/*/SKILL.md` - Skill definitions
- `skills/*/scripts/` - Skill scripts
- `skills/*/config/` - Skill configs (excluding sensitive)

### 6. Deployment Manifests
- `emotiond-api/deploy/` - Kubernetes manifests
- `emotiond-api/deployment-package/` - Deployment docs

### 7. Hooks
- `hooks/*` - Git hooks and enforcers

## Estimated Count
- Core source: ~150 files
- Config/templates: ~20 files
- Docs: ~100 files
- Skills: ~200 files
- Tests: ~50 files
- Other: ~30 files

**Total to keep**: ~550 files (out of 3,871)
