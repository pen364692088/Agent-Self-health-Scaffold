#!/bin/bash
# Repository Scope Check
# Validates repository content against CANONICAL_SCOPE.md
# Exit 1 if violations found

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
VIOLATIONS=0

echo "=== Repository Scope Check ==="
echo ""

# Forbidden directories
FORBIDDEN_DIRS=(
    "OpenEmotion"
    "OpenEmotion_MVP5"
    ".openviking-data-local-ollama"
    ".openviking"
    "modules"
    "checkpoints"
    "logs"
)

# Forbidden root files
FORBIDDEN_ROOT_FILES=(
    "cerebras_config.json"
    "config/prompt_pilot.json"
)

# Forbidden artifact patterns
FORBIDDEN_ARTIFACTS=(
    "artifacts/context_compression"
    "artifacts/distilled"
    "artifacts/integration"
    "artifacts/openviking"
    "artifacts/prompt_pilot"
    "artifacts/prompt_preview"
    "artifacts/recovery_preview"
    "artifacts/shadow_compare"
    "artifacts/auto_resume"
    "artifacts/self_health"
    "artifacts/session_reuse"
    "artifacts/test_tmp"
    "artifacts/materialized_state"
)

echo "Checking forbidden directories..."
for dir in "${FORBIDDEN_DIRS[@]}"; do
    if [ -d "$REPO_ROOT/$dir" ]; then
        echo "❌ VIOLATION: Found forbidden directory: $dir"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

echo "Checking forbidden root files..."
for file in "${FORBIDDEN_ROOT_FILES[@]}"; do
    if [ -f "$REPO_ROOT/$file" ]; then
        echo "❌ VIOLATION: Found forbidden file: $file"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

echo "Checking forbidden artifact patterns..."
for pattern in "${FORBIDDEN_ARTIFACTS[@]}"; do
    if [ -d "$REPO_ROOT/$pattern" ]; then
        echo "❌ VIOLATION: Found forbidden artifact: $pattern"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

echo "Checking for .jsonl files at root level..."
jsonl_count=$(find "$REPO_ROOT" -maxdepth 1 -name "*.jsonl" -type f 2>/dev/null | wc -l)
if [ "$jsonl_count" -gt 0 ]; then
    echo "❌ VIOLATION: Found $jsonl_count .jsonl files at root level"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

echo "Checking for runtime code in core/..."
if [ -d "$REPO_ROOT/core" ]; then
    runtime_files=$(find "$REPO_ROOT/core" -name "*.py" -type f 2>/dev/null | grep -v __pycache__ | wc -l)
    if [ "$runtime_files" -gt 0 ]; then
        echo "❌ VIOLATION: Found $runtime_files runtime .py files in core/"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
fi

echo ""
echo "=== Summary ==="

if [ "$VIOLATIONS" -eq 0 ]; then
    echo "✅ PASSED: No scope violations found"
    exit 0
else
    echo "❌ FAILED: Found $VIOLATIONS scope violation(s)"
    echo ""
    echo "Refer to: docs/repo-governance/CANONICAL_SCOPE.md"
    exit 1
fi
