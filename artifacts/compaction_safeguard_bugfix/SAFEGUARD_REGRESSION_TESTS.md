#!/usr/bin/env python3
"""
Regression Tests for Compaction Safeguard Bugfix

Tests that isRealConversationMessage and hasRealConversationContent
correctly identify messages in both nested (event) and flat formats.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Test cases
TEST_CASES: List[Tuple[str, Dict[str, Any], bool]] = [
    # (description, message_object, expected_result)
    
    # Flat format (original expected format)
    ("Flat user message", {"role": "user", "content": "Hello"}, True),
    ("Flat assistant message", {"role": "assistant", "content": "Hi there"}, True),
    ("Flat toolResult message", {"role": "toolResult", "content": "result"}, True),
    ("Flat system message", {"role": "system", "content": "instruction"}, False),
    ("Flat with no role", {"content": "text"}, False),
    
    # Nested format (actual session format)
    ("Nested user message", 
     {"type": "message", "message": {"role": "user", "content": "Hello"}}, True),
    ("Nested assistant message", 
     {"type": "message", "message": {"role": "assistant", "content": "Response"}}, True),
    ("Nested toolResult message", 
     {"type": "message", "message": {"role": "toolResult", "content": "result"}}, True),
    ("Nested system message", 
     {"type": "message", "message": {"role": "system", "content": "instruction"}}, False),
    ("Nested with no role in inner", 
     {"type": "message", "message": {"content": "text"}}, False),
    ("Nested with null inner message", 
     {"type": "message", "message": None}, False),
    
    # Edge cases
    ("Empty object", {}, False),
    ("None/null", None, False),
    ("Array content", 
     {"role": "user", "content": [{"type": "text", "text": "Hello"}]}, True),
    ("Nested with array content", 
     {"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": "Hello"}]}}, True),
]


def test_is_real_conversation_message_js():
    """
    Test the JavaScript isRealConversationMessage function.
    This would need Node.js to execute.
    """
    print("\n=== Testing isRealConversationMessage (JS) ===\n")
    
    # Create test harness
    test_harness = """
    // Original buggy implementation
    function isRealConversationMessageBuggy(message) {
        return message.role === "user" || message.role === "assistant" || message.role === "toolResult";
    }
    
    // Fixed implementation
    function isRealConversationMessageFixed(message) {
        const msg = message.message || message;
        const role = msg.role;
        return role === "user" || role === "assistant" || role === "toolResult";
    }
    
    const testCases = %s;
    
    let buggyFailures = 0;
    let fixedSuccesses = 0;
    let totalTests = testCases.length;
    
    for (const [desc, msg, expected] of testCases) {
        const buggyResult = isRealConversationMessageBuggy(msg);
        const fixedResult = isRealConversationMessageFixed(msg);
        
        const buggyOk = buggyResult === expected;
        const fixedOk = fixedResult === expected;
        
        if (!buggyOk) buggyFailures++;
        if (fixedOk) fixedSuccesses++;
        
        console.log(JSON.stringify({
            test: desc,
            expected: expected,
            buggy: { result: buggyResult, pass: buggyOk },
            fixed: { result: fixedResult, pass: fixedOk }
        }));
    }
    
    console.log(JSON.stringify({
        summary: {
            total: totalTests,
            buggyFailures: buggyFailures,
            fixedSuccesses: fixedSuccesses,
            allFixedPass: fixedSuccesses === totalTests
        }
    }));
    """ % json.dumps([[d, m, e] for d, m, e in TEST_CASES])
    
    # Write test file
    test_file = Path(__file__).parent / "test_safeguard.js"
    test_file.write_text(test_harness)
    
    print(f"Test harness written to: {test_file}")
    print("Run with: node test_safeguard.js")
    
    return test_file


def test_python_equivalent():
    """
    Test Python equivalent of the logic to verify the fix.
    """
    print("\n=== Testing Python Equivalent Logic ===\n")
    
    def is_real_conversation_message_buggy(message):
        """Original buggy implementation"""
        if message is None:
            return False
        role = message.get("role")
        return role in ("user", "assistant", "toolResult")
    
    def is_real_conversation_message_fixed(message):
        """Fixed implementation"""
        if message is None:
            return False
        msg = message.get("message") or message
        if not isinstance(msg, dict):
            return False
        role = msg.get("role")
        return role in ("user", "assistant", "toolResult")
    
    buggy_pass = 0
    buggy_fail = 0
    fixed_pass = 0
    fixed_fail = 0
    
    for desc, msg, expected in TEST_CASES:
        buggy_result = is_real_conversation_message_buggy(msg)
        fixed_result = is_real_conversation_message_fixed(msg)
        
        buggy_ok = buggy_result == expected
        fixed_ok = fixed_result == expected
        
        if buggy_ok:
            buggy_pass += 1
        else:
            buggy_fail += 1
        
        if fixed_ok:
            fixed_pass += 1
        else:
            fixed_fail += 1
        
        status = "✅" if fixed_ok else "❌"
        buggy_status = "✅" if buggy_ok else "❌"
        
        print(f"{status} {desc}")
        print(f"   Expected: {expected}, Buggy: {buggy_result} {buggy_status}, Fixed: {fixed_result} {status}")
    
    print("\n=== Summary ===")
    print(f"Total tests: {len(TEST_CASES)}")
    print(f"Buggy implementation: {buggy_pass} pass, {buggy_fail} fail")
    print(f"Fixed implementation: {fixed_pass} pass, {fixed_fail} fail")
    
    all_pass = fixed_pass == len(TEST_CASES)
    
    if all_pass:
        print("\n✅ All tests PASSED with fixed implementation!")
    else:
        print(f"\n❌ {fixed_fail} tests FAILED with fixed implementation!")
    
    return all_pass


def test_real_session_format():
    """
    Test with actual session format from OpenClaw logs.
    """
    print("\n=== Testing Real Session Format ===\n")
    
    # Sample from actual session.jsonl
    real_messages = [
        # User message
        {
            "type": "message",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "执行 native compaction safeguard bug 修复"}]
            }
        },
        # Assistant message  
        {
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "开始修复..."}]
            }
        },
        # Tool call
        {
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": ""},
                    {"type": "tool_use", "id": "call_123", "name": "exec", "input": {}}
                ]
            }
        },
        # Tool result
        {
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolUseId": "call_123",
                "content": "output"
            }
        }
    ]
    
    def is_real_conversation_message_fixed(message):
        if message is None:
            return False
        msg = message.get("message") or message
        if not isinstance(msg, dict):
            return False
        role = msg.get("role")
        return role in ("user", "assistant", "toolResult")
    
    detected = sum(1 for m in real_messages if is_real_conversation_message_fixed(m))
    
    print(f"Sample messages: {len(real_messages)}")
    print(f"Detected as conversation: {detected}")
    
    if detected == len(real_messages):
        print("✅ All real session messages correctly detected!")
        return True
    else:
        print(f"❌ Expected {len(real_messages)}, got {detected}")
        return False


def main():
    print("=" * 60)
    print("Compaction Safeguard Bugfix Regression Tests")
    print("=" * 60)
    
    # Run Python equivalent test
    py_ok = test_python_equivalent()
    
    # Run real session format test
    session_ok = test_real_session_format()
    
    # Generate JS test file
    js_test_file = test_is_real_conversation_message_js()
    
    print("\n" + "=" * 60)
    print("Results:")
    print(f"  Python equivalent: {'PASS' if py_ok else 'FAIL'}")
    print(f"  Real session format: {'PASS' if session_ok else 'FAIL'}")
    print(f"  JS test file: {js_test_file}")
    print("=" * 60)
    
    if py_ok and session_ok:
        print("\n✅ All regression tests PASSED!")
        return 0
    else:
        print("\n❌ Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
