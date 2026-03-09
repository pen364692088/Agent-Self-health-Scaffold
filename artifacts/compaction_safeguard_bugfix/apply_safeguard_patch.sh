#!/bin/bash
# Compaction Safeguard Bugfix Patch
# Fixes: Safeguard incorrectly rejects messages due to format mismatch
# Issue: Checks message.role at top level, but actual data is in message.message.role

set -e

COMPACT_FILE="$HOME/.npm-global/lib/node_modules/openclaw/dist/compact-B247y5Qt.js"
BACKUP_FILE="${COMPACT_FILE}.original"

if [ ! -f "$COMPACT_FILE" ]; then
    echo "ERROR: compact file not found at $COMPACT_FILE"
    exit 1
fi

# Create backup if not exists
if [ ! -f "$BACKUP_FILE" ]; then
    cp "$COMPACT_FILE" "$BACKUP_FILE"
    echo "Created backup: $BACKUP_FILE"
fi

# Fix isRealConversationMessage (line 13666)
# Before: return message.role === "user" || message.role === "assistant" || message.role === "toolResult";
# After:  const msg = message.message || message; return msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult";

sed -i 's/function isRealConversationMessage(message) {/function isRealConversationMessage(message) {\n\t\/\/ PATCHED: Support both nested (event) and flat message formats\n\tconst msg = message.message || message;/' "$COMPACT_FILE"

sed -i 's/return message.role === "user" || message.role === "assistant" || message.role === "toolResult";/return msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult";/' "$COMPACT_FILE"

# Fix hasRealConversationContent (line 92957)
# Same pattern as above

# Find the exact line for hasRealConversationContent
LINE_NUM=$(grep -n "^function hasRealConversationContent" "$COMPACT_FILE" | cut -d: -f1)
if [ -n "$LINE_NUM" ]; then
    # Use awk to modify the function
    awk -v line="$LINE_NUM" '
    NR == line {
        print $0
        print "\t// PATCHED: Support both nested (event) and flat message formats"
        print "\tconst msg = message.message || message;"
        next
    }
    /return message.role === "user" \|\| message.role === "assistant" \|\| message.role === "toolResult";/ {
        gsub(/return message\.role/, "return msg.role")
    }
    { print }
    ' "$COMPACT_FILE" > "${COMPACT_FILE}.tmp" && mv "${COMPACT_FILE}.tmp" "$COMPACT_FILE"
fi

echo "Patch applied successfully"
echo "Backup saved at: $BACKUP_FILE"
echo "To restore: cp $BACKUP_FILE $COMPACT_FILE"
