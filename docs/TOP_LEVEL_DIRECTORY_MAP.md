# Top-Level Directory Map

**Generated**: 2026-03-14
**Purpose**: Classify repository directories by role and maintenance status

---

## Directory Classification

### 🟢 Main Execution Kernel (Core)

| Directory | Role | Status |
|-----------|------|--------|
| `core/` | Core modules (MaterializedState, adapters, preview) | ✅ Active |
| `tests/` | Test suite (123 tests) | ✅ Active |
| `tools/` | CLI tools (materialize-state, prompt-pilot-*) | ✅ Active |
| `config/` | Configuration files | ✅ Active |
| `schemas/` | JSON schemas | ✅ Frozen |
| `state/` | Runtime state files | ✅ Active |

### 📚 Documentation & Policy

| Directory | Role | Status |
|-----------|------|--------|
| `docs/` | Documentation (runbooks, scope docs) | ✅ Active |
| `POLICIES/` | Policy documents | ✅ Active |
| `RUNBOOKS/` | Operational runbooks | ✅ Active |

### 🔄 Runtime & Artifacts

| Directory | Role | Status |
|-----------|------|--------|
| `artifacts/` | Runtime artifacts (metrics, previews, reports) | ✅ Active |
| `logs/` | Log files | ✅ Active |
| `reports/` | Generated reports | ✅ Active |
| `checkpoints/` | Execution checkpoints | ✅ Active |
| `session-archives/` | Session history | ✅ Active |

### 🧪 Experimental / External Projects

| Directory | Role | Status | Recommendation |
|-----------|------|--------|----------------|
| `OpenEmotion/` | Emotion tracking experiment | 🔶 Experimental | Consider isolation |
| `OpenEmotion_MVP5/` | Emotion MVP version | 🔶 Experimental | Consider consolidation |
| `emotiond/` | Emotion daemon | 🔶 Experimental | Consider isolation |
| `emotiond-api/` | Emotion API | 🔶 Experimental | Consider isolation |
| `searxng-docker/` | Search engine integration | 🔶 External | Consider isolation |
| `openviking/` | Viking memory system | 🔶 External | Consider isolation |
| `trust-anchor/` | Trust system | 🔶 Experimental | Consider isolation |
| `think-cog/` | Thinking system | 🔶 Experimental | Consider isolation |
| `daily-briefing/` | Briefing generator | 🔶 Experimental | Consider isolation |

### 📦 Supporting Infrastructure

| Directory | Role | Status |
|-----------|------|--------|
| `api/` | API endpoints | ✅ Active |
| `scripts/` | Utility scripts | ✅ Active |
| `templates/` | Template files | ✅ Active |
| `hooks/` | Git hooks | ✅ Active |
| `flows/` | Flow definitions | ✅ Active |
| `pipelines/` | Pipeline definitions | ✅ Active |
| `runtime/` | Runtime components | ✅ Active |
| `src/` | Source files | ✅ Active |
| `memory/` | Memory storage | ✅ Active |
| `metrics/` | Metrics collection | ✅ Active |
| `notes/` | Note storage | ✅ Active |
| `agents/` | Agent definitions | ✅ Active |
| `skills/` | Skill definitions | ✅ Active |

### ⚪ Infrastructure / Hidden

| Directory | Role | Status |
|-----------|------|--------|
| `.git/` | Git repository | ✅ Required |
| `.github/` | GitHub config | ✅ Required |
| `.openclaw/` | OpenClaw config | ✅ Required |
| `.pytest_cache/` | Pytest cache | ⚪ Generated |
| `.repo-audit/` | Audit files | ⚪ Generated |
| `.session-index/` | Session index | ⚪ Generated |
| `.openviking-data*/` | Viking data | ⚪ Generated |
| `.pi/` | Pi config | ⚪ Generated |
| `.prose/` | Prose config | ⚪ Generated |
| `.clawhub/` | ClawHub cache | ⚪ Generated |
| `tmp/` | Temporary files | ⚪ Temporary |

---

## Recommendations

### Low Risk (Can do now)
1. ✅ Add `CURRENT_STATUS.md` as single source of truth (DONE)
2. ✅ Update `README.md` to reflect current state (DONE)
3. ✅ Clarify config field relationships (DONE)

### Medium Risk (Plan first)
1. 📋 Consider creating `experiments/` for external projects
2. 📋 Consider consolidating `OpenEmotion*` directories
3. 📋 Consider adding `.gitignore` entries for generated directories

### High Risk (Requires migration plan)
1. ⚠️ Moving any directory requires updating all imports
2. ⚠️ Consolidating projects requires stakeholder approval
3. ⚠️ Large-scale reorganization should be separate task

---

## Summary Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| Main Kernel | 6 | 15% |
| Documentation | 3 | 7% |
| Runtime/Artifacts | 5 | 12% |
| Experimental | 9 | 22% |
| Supporting | 14 | 34% |
| Infrastructure | 10 | 24% |
| **Total** | **41** | 100% |

---

## File: docs/TOP_LEVEL_DIRECTORY_MAP.md
