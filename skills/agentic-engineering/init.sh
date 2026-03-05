#!/bin/bash
# Agentic Engineering Skill - Init Wrapper
# This is now a thin wrapper around LongRunKit

set -e

TARGET="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Call LongRunKit
if command -v longrun &> /dev/null; then
    longrun init --project "$TARGET" --with-agentic
else
    # Fallback to direct path
    ~/.local/bin/longrun init --project "$TARGET" --with-agentic
fi
