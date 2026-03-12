# Compaction Capability Group Addition

## Summary

Added 3 new capabilities to monitor native compaction health.

## Added Capabilities

### P0 - Critical

| Capability | Category | Description |
|------------|----------|-------------|
| CAP-COMPACTION_EXECUTION | core_feature | Checks if compaction runs and succeeds |
| CAP-CONTEXT_OVERFLOW_HANDLING | safety | Checks if context overflow is properly handled |

### P1 - High

| Capability | Category | Description |
|------------|----------|-------------|
| CAP-COMPACTION_EFFECTIVENESS | core_feature | Checks if compaction is effective |

## Detection Logic

### CAP-COMPACTION_EXECUTION
- Checks compaction counter
- Checks for recent compaction entries
- Verifies RESTORED status

### CAP-CONTEXT_OVERFLOW_HANDLING
- Monitors session context ratios
- Detects high pressure sessions (>80%)
- Checks for lane/blocker issues

### CAP-COMPACTION_EFFECTIVENESS
- Verifies compaction runs exist
- Checks OpenViking retrieval availability
- Validates compaction + retrieval chain

## Why This Matters

Before this addition, the self-health scaffold did not monitor compaction at all.
This gap meant the system could have broken compaction without any alert.

Now compaction is a first-class capability with:
- Execution monitoring (does it run?)
- Overflow handling (does it trigger when needed?)
- Effectiveness monitoring (does it work?)

## Alert Rules

| Condition | Priority | Action |
|-----------|----------|--------|
| Execution != healthy | **CRITICAL** | Immediate investigation |
| Overflow Handling != healthy | **CRITICAL** | Immediate investigation |
| Effectiveness != healthy | HIGH | Review within 1 hour |

## Current Status

All 3 new capabilities: ✅ HEALTHY

## Scope Statement

**后续与 compaction execution / overflow handling / effectiveness 相关的主要问题，已经纳入自动检测范围。**

Note: This does not claim to detect "all possible problems". It covers the main failure modes that have been identified and instrumented.

---

**Generated**: 2026-03-09 05:38 CST
