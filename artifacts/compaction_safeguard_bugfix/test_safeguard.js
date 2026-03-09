
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
    
    const testCases = [["Flat user message", {"role": "user", "content": "Hello"}, true], ["Flat assistant message", {"role": "assistant", "content": "Hi there"}, true], ["Flat toolResult message", {"role": "toolResult", "content": "result"}, true], ["Flat system message", {"role": "system", "content": "instruction"}, false], ["Flat with no role", {"content": "text"}, false], ["Nested user message", {"type": "message", "message": {"role": "user", "content": "Hello"}}, true], ["Nested assistant message", {"type": "message", "message": {"role": "assistant", "content": "Response"}}, true], ["Nested toolResult message", {"type": "message", "message": {"role": "toolResult", "content": "result"}}, true], ["Nested system message", {"type": "message", "message": {"role": "system", "content": "instruction"}}, false], ["Nested with no role in inner", {"type": "message", "message": {"content": "text"}}, false], ["Nested with null inner message", {"type": "message", "message": null}, false], ["Empty object", {}, false], ["None/null", null, false], ["Array content", {"role": "user", "content": [{"type": "text", "text": "Hello"}]}, true], ["Nested with array content", {"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": "Hello"}]}}, true]];
    
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
    