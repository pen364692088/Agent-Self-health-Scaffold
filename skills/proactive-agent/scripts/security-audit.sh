#!/bin/bash

# Proactive Agent Security Audit Script
# Scans workspace for security issues and configuration problems

set -euo pipefail

echo "🔍 Proactive Agent Security Audit"
echo "================================="
echo

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ISSUES_FOUND=0

# Function to log issues
log_issue() {
    local severity=$1
    local message=$2
    local file=${3:-""}
    
    case $severity in
        "CRITICAL")
            echo -e "${RED}🔴 CRITICAL: $message${NC}"
            ISSUES_FOUND=$((ISSUES_FOUND + 3))
            ;;
        "HIGH")
            echo -e "${YELLOW}🟠 HIGH: $message${NC}"
            ISSUES_FOUND=$((ISSUES_FOUND + 2))
            ;;
        "MEDIUM")
            echo -e "${YELLOW}🟡 MEDIUM: $message${NC}"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            ;;
        "LOW")
            echo -e "${BLUE}🔵 LOW: $message${NC}"
            ;;
    esac
    
    if [[ -n "$file" ]]; then
        echo "   File: $file"
    fi
    echo
}

# Check for exposed credentials
echo "🔑 Checking for exposed credentials..."
if grep -r -i "api[_-]?key\|secret\|password\|token" . --include="*.md" --include="*.json" --include="*.sh" --exclude-dir=".git" 2>/dev/null | grep -v "example\|placeholder\|your_\|xxx\|***" | head -5; then
    log_issue "HIGH" "Potential exposed credentials found"
fi

# Check for dangerous shell commands
echo "💻 Checking for dangerous shell commands..."
DANGEROUS_PATTERNS=(
    "curl.*|.*bash"
    "wget.*|.*sh"
    "chmod.*+x.*&&"
    "sudo.*rm"
    "rm.*-rf.*/"
    ">:.*\*\*"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if grep -r "$pattern" . --include="*.sh" --include="*.md" --exclude-dir=".git" 2>/dev/null; then
        log_issue "HIGH" "Dangerous shell command pattern: $pattern"
    fi
done

# Check for external network connections in skills
echo "🌐 Checking skill files for external network calls..."
if find . -name "SKILL.md" -exec grep -l "http\|curl\|wget\|fetch" {} \; 2>/dev/null; then
    log_issue "MEDIUM" "Skills contain external network calls - review for safety"
fi

# Check memory file permissions
echo "📁 Checking memory file permissions..."
if [[ -f "MEMORY.md" ]]; then
    if stat -c "%a" MEMORY.md | grep -q "[467]"; then
        log_issue "MEDIUM" "MEMORY.md has overly permissive permissions"
    fi
fi

# Check for unsigned executables in scripts directory
echo "🔧 Checking for unsigned executables..."
if find scripts/ -type f -executable 2>/dev/null | head -3; then
    log_issue "MEDIUM" "Executable files found in scripts directory"
fi

# Check for missing SESSION-STATE.md
echo "📝 Checking memory architecture..."
if [[ ! -f "SESSION-STATE.md" ]]; then
    log_issue "MEDIUM" "SESSION-STATE.md missing - WAL protocol not active"
fi

# Check workspace structure
echo "🏗️ Checking workspace structure..."
REQUIRED_FILES=("SOUL.md" "USER.md" "AGENTS.md")
for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        log_issue "HIGH" "Required file missing: $file"
    fi
done

# Check for cron jobs with security implications
echo "⏰ Checking cron job security..."
if command -v openclaw >/dev/null 2>&1; then
    if openclaw cron list 2>/dev/null | grep -i "rm\|delete\|sudo"; then
        log_issue "HIGH" "Cron jobs contain potentially dangerous commands"
    fi
fi

# Check for large files that might indicate data exfiltration
echo "📊 Checking for unusually large files..."
LARGE_FILES=$(find . -type f -size +10M -not -path "./.git/*" 2>/dev/null | head -3)
if [[ -n "$LARGE_FILES" ]]; then
    log_issue "LOW" "Large files found - review if legitimate"
    echo "$LARGE_FILES"
fi

# Check for suspicious URLs
echo "🔗 Checking for suspicious URLs..."
SUSPICIOUS_DOMAINS=(
    "pastebin"
    "t\.me"
    "discord\.com.*api"
    "webhook"
)

for domain in "${SUSPICIOUS_DOMAINS[@]}"; do
    if grep -r "$domain" . --include="*.md" --include="*.json" --exclude-dir=".git" 2>/dev/null; then
        log_issue "MEDIUM" "Suspicious domain found: $domain"
    fi
done

# Summary
echo "📋 Audit Summary"
echo "==============="
if [[ $ISSUES_FOUND -eq 0 ]]; then
    echo -e "${GREEN}✅ No security issues found!${NC}"
else
    echo -e "${RED}⚠️  Issues found (severity score: $ISSUES_FOUND)${NC}"
    echo
    echo "Recommended actions:"
    if [[ $ISSUES_FOUND -ge 6 ]]; then
        echo -e "${RED}• CRITICAL: Address immediately${NC}"
    elif [[ $ISSUES_FOUND -ge 3 ]]; then
        echo -e "${YELLOW}• HIGH: Review and fix soon${NC}"
    else
        echo -e "${BLUE}• LOW: Consider addressing when convenient${NC}"
    fi
fi

echo
echo "🔒 Security audit completed"