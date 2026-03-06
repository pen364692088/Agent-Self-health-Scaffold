# Project Check Pipeline Specification

**Version:** 1.0.0  
**Last Updated:** 2026-03-06  
**Status:** Draft

## Overview

The Project Check Pipeline is a multi-phase validation system for automated project health checks. It executes a series of checks against a project repository and produces structured reports with actionable insights.

## Goals

1. **Standardization**: Provide a consistent, schema-driven approach to project validation
2. **Extensibility**: Support multiple phases with dependency management
3. **Observability**: Generate structured artifacts for every check run
4. **Reliability**: Handle failures gracefully with retry and continuation support

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Project Check Pipeline                     │
├─────────────────────────────────────────────────────────────┤
│  Orchestrator                                                │
│  ├── Manifest Loader (reads manifest.json)                   │
│  ├── Phase Runner (executes phases in order)                 │
│  ├── Status Tracker (writes status.json per phase)           │
│  └── Report Generator (creates final report)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase Runners                                               │
│  ├── Phase A: Repository Health Check                        │
│  ├── Phase B: Test Suite Execution                           │
│  ├── Phase C: Testbot Validation                             │
│  └── Phase D: Final Gate Check                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Schemas

### manifest.json

**Purpose**: Defines the check execution plan

**Schema**: `schemas/project_check_manifest.v1.schema.json`

**Key Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `check_id` | string | ✓ | Unique identifier (format: `check_YYYYMMDD_HHMMSS_<hash>`) |
| `created_at` | datetime | ✓ | ISO8601 timestamp |
| `project_path` | string | ✓ | Absolute path to project |
| `phases` | array | ✓ | Ordered list of phase definitions |
| `config` | object | ✓ | Global configuration |

**Phase Definition**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | enum | ✓ | - | Phase identifier |
| `name` | string | ✓ | - | Human-readable name |
| `runner` | string | ✓ | - | Command to execute |
| `artifacts_dir` | string | ✓ | - | Output directory name |
| `depends_on` | array | - | [] | Prerequisite phases |
| `stop_on_fail` | bool | - | true | Stop pipeline on failure |
| `timeout_seconds` | int | - | 300 | Max execution time |

### status.json

**Purpose**: Tracks per-phase execution state

**Schema**: `schemas/project_check_status.v1.schema.json`

**Key Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phase` | enum | ✓ | Phase identifier |
| `state` | enum | ✓ | `pending`, `running`, `done`, `failed`, `skipped` |
| `ok` | bool | ✓ | Overall success status |
| `started_at` | datetime | - | Execution start time |
| `finished_at` | datetime | - | Execution end time |
| `inputs` | object | ✓ | Input parameters (branch, commit, etc.) |
| `metrics` | object | - | Phase-specific metrics |
| `artifacts` | object | - | Paths to generated files |
| `next_action` | string | - | Suggested next step |
| `error` | object | - | Error details if failed |

---

## Directory Structure

```
artifacts/project_check/<check_id>/
├── manifest.json                 # Copy of the execution manifest
├── phase_a_repo/
│   ├── status.json               # Phase A status
│   ├── summary.md                # Human-readable summary
│   └── raw.log                   # Full execution log
├── phase_b_tests/
│   ├── status.json
│   ├── summary.md
│   ├── raw.log
│   └── coverage/                 # Test coverage report (if generated)
├── phase_c_testbot/
│   ├── status.json
│   ├── summary.md
│   └── raw.log
├── phase_d_gate/
│   ├── status.json
│   ├── summary.md
│   └── raw.log
└── final/
    ├── FINAL_CHECK_STATUS.json   # Overall pipeline status
    ├── FINAL_CHECK_REPORT.md     # Consolidated report
    └── one_liner.txt             # Single-line result summary
```

---

## Phase Definitions

### Phase A: Repository Health Check

**ID**: `phase_a_repo`  
**Purpose**: Validate repository structure, configuration, and basic health

**Checks**:
- Git repository validity
- Branch status (clean working tree)
- Configuration files present
- Dependencies up-to-date
- Code style compliance

**Metrics**:
- `files_checked`: Number of files scanned
- `issues_found`: Total issues detected
- `warnings_count`: Non-critical warnings

### Phase B: Test Suite Execution

**ID**: `phase_b_tests`  
**Dependencies**: `phase_a_repo`  
**Purpose**: Run the project's test suite

**Checks**:
- Test runner availability
- Test execution
- Coverage analysis
- Failed test identification

**Metrics**:
- `tests_total`: Total tests
- `tests_passed`: Passed tests
- `tests_failed`: Failed tests
- `coverage_percent`: Code coverage

### Phase C: Testbot Validation

**ID**: `phase_c_testbot`  
**Dependencies**: `phase_b_tests`  
**Purpose**: Run testbot-specific validations

**Checks**:
- Testbot configuration
- Integration tests
- End-to-end scenarios

**Metrics**:
- Varies by project

### Phase D: Final Gate Check

**ID**: `phase_d_gate`  
**Dependencies**: All previous phases  
**Purpose**: Final validation and report generation

**Checks**:
- All previous phases passed
- Quality gates met
- Documentation updated

**Metrics**:
- `overall_score`: Composite quality score

---

## Execution Flow

### Standard Flow

```
1. Initialize check run
   ├── Generate check_id
   ├── Create artifact directory
   └── Write manifest.json

2. Execute phases in order (respecting dependencies)
   ├── For each phase:
   │   ├── Create phase directory
   │   ├── Write status.json (state=running)
   │   ├── Execute runner
   │   ├── Capture output
   │   ├── Write status.json (state=done|failed)
   │   └── Write summary.md and raw.log
   └── Handle failures per stop_on_fail policy

3. Generate final report
   ├── Collect all status.json files
   ├── Determine overall status
   ├── Write FINAL_CHECK_STATUS.json
   ├── Write FINAL_CHECK_REPORT.md
   └── Write one_liner.txt

4. Cleanup (optional)
   └── Remove old artifacts based on retention policy
```

### Failure Handling

```
Phase fails:
├── If stop_on_fail = true:
│   ├── Stop pipeline execution
│   └── Set remaining phases to skipped
└── If stop_on_fail = false:
    ├── Log failure
    └── Continue to next phase

Retry logic:
├── Check max_retries config
├── Retry failed phase up to max_retries
└── Track retry_count in error object
```

---

## API Reference

### Create Check Run

```bash
project-check init <project_path> [--config <config_file>]
```

**Output**: `check_id`

### Run Single Phase

```bash
project-check run-phase <check_id> <phase_id>
```

**Output**: Updated `status.json`

### Run Full Pipeline

```bash
project-check run <check_id>
```

**Output**: Final artifacts in `final/` directory

### Get Status

```bash
project-check status <check_id>
```

**Output**: JSON with all phase statuses

---

## Error Codes

| Code | Description | Recovery Action |
|------|-------------|-----------------|
| `TIMEOUT` | Phase exceeded time limit | Increase timeout or optimize phase |
| `COMMAND_FAILED` | Runner command returned non-zero | Check raw.log for details |
| `VALIDATION_ERROR` | Input validation failed | Fix manifest.json |
| `DEPENDENCY_FAILED` | Required phase failed | Fix upstream phase first |
| `NOT_FOUND` | Required file/directory missing | Check project structure |
| `PERMISSION_DENIED` | Insufficient permissions | Check file permissions |

---

## Configuration

### Default Configuration

```json
{
  "timeout_per_phase": 300,
  "max_retries": 0,
  "artifact_root": "artifacts/project_check",
  "continue_on_failure": false,
  "parallel_phases": false
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_CHECK_DEBUG` | Enable debug logging | `0` |
| `PROJECT_CHECK_ARTIFACT_ROOT` | Override artifact root | From config |
| `PROJECT_CHECK_TIMEOUT` | Default timeout override | From config |

---

## Integration

### CLI Usage

```bash
# Full check
project-check /path/to/project

# Specific phases
project-check /path/to/project --phases phase_a_repo,phase_b_tests

# Dry run
project-check /path/to/project --dry-run
```

### Programmatic Usage

```python
from project_check import Pipeline

pipeline = Pipeline("/path/to/project")
pipeline.run()
print(pipeline.final_status)
```

---

## Versioning

- Schema version: `v1` (current)
- Breaking changes require new schema version (v2, v3, etc.)
- Backward compatibility maintained within major version
- Schema changes documented in CHANGELOG.md

---

## References

- JSON Schema Draft-07: https://json-schema.org/specification-links.html#draft-7
- Project Check Workflow: See SESSION-STATE.md
- Tool Delivery Gates: See POLICIES/TOOL_DELIVERY.md

---

## Changelog

### v1.0.0 (2026-03-06)
- Initial specification
- Defined manifest.json schema
- Defined status.json schema
- Specified 4-phase pipeline structure
