#!/usr/bin/env python3
"""
Compaction Safeguard Bugfix Patch
Direct patch for OpenClaw's compact module to fix message detection.

Bug: isRealConversationMessage and hasRealConversationContent only check
top-level message.role, but actual messages are nested in message.message.

Fix: Support both formats by checking message.message first.
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

def main():
    compact_file = Path.home() / ".npm-global/lib/node_modules/openclaw/dist/compact-B247y5Qt.js"
    backup_file = compact_file.with_suffix(".js.original")
    
    if not compact_file.exists():
        print(f"ERROR: File not found: {compact_file}")
        return 1
    
    # Create backup
    if not backup_file.exists():
        backup_file.write_text(compact_file.read_text())
        print(f"Created backup: {backup_file}")
    
    content = compact_file.read_text()
    original_content = content
    
    # Fix 1: isRealConversationMessage function
    # Pattern: function isRealConversationMessage(message) {
    #          return message.role === "user" || message.role === "assistant" || message.role === "toolResult";
    #          }
    
    pattern1 = r'''function isRealConversationMessage\(message\) \{
\treturn message\.role === "user" \|\| message\.role === "assistant" \|\| message\.role === "toolResult";
\}'''
    
    replacement1 = '''function isRealConversationMessage(message) {
\t// PATCHED: Support both nested (event) and flat message formats
\tconst msg = message.message || message;
\treturn msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult";
}'''
    
    content = re.sub(pattern1, replacement1, content)
    
    # Also handle the case without leading tab
    pattern1b = r'''function isRealConversationMessage\(message\) \{
return message\.role === "user" \|\| message\.role === "assistant" \|\| message\.role === "toolResult";
\}'''
    
    replacement1b = '''function isRealConversationMessage(message) {
\t// PATCHED: Support both nested (event) and flat message formats
\tconst msg = message.message || message;
\treturn msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult";
}'''
    
    content = re.sub(pattern1b, replacement1b, content)
    
    # Fix 2: hasRealConversationContent function
    # Pattern: function hasRealConversationContent(msg) {
    #          return msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult";
    #          }
    
    pattern2 = r'''function hasRealConversationContent\(msg\) \{
\treturn msg\.role === "user" \|\| msg\.role === "assistant" \|\| msg\.role === "toolResult";
\}'''
    
    replacement2 = '''function hasRealConversationContent(msg) {
\t// PATCHED: Support both nested (event) and flat message formats
\tconst m = msg.message || msg;
\treturn m.role === "user" || m.role === "assistant" || m.role === "toolResult";
}'''
    
    content = re.sub(pattern2, replacement2, content)
    
    # Also handle the case without leading tab
    pattern2b = r'''function hasRealConversationContent\(msg\) \{
return msg\.role === "user" \|\| msg\.role === "assistant" \|\| msg\.role === "toolResult";
\}'''
    
    replacement2b = '''function hasRealConversationContent(msg) {
\t// PATCHED: Support both nested (event) and flat message formats
\tconst m = msg.message || msg;
\treturn m.role === "user" || m.role === "assistant" || m.role === "toolResult";
}'''
    
    content = re.sub(pattern2b, replacement2b, content)
    
    if content == original_content:
        print("WARNING: No changes made. Patterns may not match.")
        print("Attempting alternative patching approach...")
        
        # Alternative: Use line-by-line approach
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
            # Find the function definition line
            if 'function isRealConversationMessage(message)' in line:
                # Next line should be the return statement
                if i + 1 < len(lines) and 'return message.role' in lines[i + 1]:
                    # Insert the const line before return
                    lines.insert(i + 1, '\t// PATCHED: Support both nested (event) and flat message formats')
                    lines.insert(i + 2, '\tconst msg = message.message || message;')
                    # Modify the return line
                    lines[i + 3] = lines[i + 3].replace('message.role', 'msg.role')
                    modified = True
                    print(f"Patched isRealConversationMessage at line {i+1}")
            
            if 'function hasRealConversationContent(msg)' in line:
                if i + 1 < len(lines) and 'return msg.role' in lines[i + 1]:
                    lines.insert(i + 1, '\t// PATCHED: Support both nested (event) and flat message formats')
                    lines.insert(i + 2, '\tconst m = msg.message || msg;')
                    lines[i + 3] = lines[i + 3].replace('msg.role', 'm.role')
                    modified = True
                    print(f"Patched hasRealConversationContent at line {i+1}")
        
        if modified:
            content = '\n'.join(lines)
        else:
            print("ERROR: Could not apply patch. Manual intervention required.")
            return 1
    
    # Write patched content
    compact_file.write_text(content)
    
    # Generate patch diff
    patch_file = Path(__file__).parent / "safeguard.patch"
    diff = generate_diff(original_content, content)
    patch_file.write_text(diff)
    
    print(f"\nPatch applied successfully!")
    print(f"  Backup: {backup_file}")
    print(f"  Patch: {patch_file}")
    print(f"\nTo restore original:")
    print(f"  cp {backup_file} {compact_file}")
    
    return 0


def generate_diff(original: str, patched: str) -> str:
    """Generate a simple diff format"""
    lines_orig = original.split('\n')
    lines_patch = patched.split('\n')
    
    diff = f"""--- a/dist/compact-B247y5Qt.js (original)
+++ b/dist/compact-B247y5Qt.js (patched)
Date: {datetime.now().isoformat()}

"""
    
    # Find changed sections
    for i, (orig, new) in enumerate(zip(lines_orig, lines_patch)):
        if orig != new:
            diff += f"@@ Line {i+1} @@\n"
            diff += f"-{orig}\n"
            diff += f"+{new}\n\n"
    
    return diff


if __name__ == "__main__":
    sys.exit(main())
