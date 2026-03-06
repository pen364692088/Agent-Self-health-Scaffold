# Self-Report Consistency Checker Integration

## Context
将 self_report_consistency_checker 集成到 emotiond-enforcer hook。

## Integration Point
`integrations/openclaw/hooks/emotiond-enforcer/handler.js`

## Requirements

### 1. CLI Wrapper for Python Checker
Create `emotiond/self_report_check.py`:
```python
#!/usr/bin/env python3
"""CLI wrapper for self_report_consistency_checker"""
import sys
import json
from emotiond.self_report_consistency_checker import check_consistency

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "no_llm_response"}))
        sys.exit(1)
    
    llm_response = sys.argv[1]
    contract_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Load contract from file or use default
    contract = None
    if contract_path:
        with open(contract_path) as f:
            contract = json.load(f)
    
    result = check_consistency(llm_response, contract)
    print(json.dumps(result.to_dict()))
```

### 2. Modify emotiond-enforcer/handler.js
Add self_report check before enforcement:
```javascript
const { execSync } = require('child_process');
const path = require('path');

const SRAP_ENABLED = process.env.SRAP_ENABLED === '1';
const SRAP_MODE = process.env.SRAP_MODE || 'shadow';
const SRAP_SHADOW_LOG = process.env.SRAP_SHADOW_LOG || 'artifacts/self_report/shadow_log.jsonl';

async function checkSelfReport(llmResponse, contractPath) {
  try {
    const pythonScript = path.join(__dirname, '../../../emotiond/self_report_check.py');
    const result = execSync(`python3 "${pythonScript}" "${llmResponse}" "${contractPath}"`, {
      encoding: 'utf8',
      timeout: 5000,
      maxBuffer: 1024 * 1024
    });
    return JSON.parse(result);
  } catch (e) {
    console.error('[emotiond-enforcer] Self-report check error:', e.message);
    return { status: 'error', error: e.message };
  }
}

// In handler:
if (SRAP_ENABLED) {
  const contractPath = path.join(WORKSPACE_DIR, 'emotiond/context.json');
  const srapResult = await checkSelfReport(proposedResponse, contractPath);
  
  if (srapResult.status === 'violation') {
    console.log('[SRAP] Violation detected:', srapResult.violations);
    
    // Shadow mode: just log
    if (SRAP_MODE === 'shadow') {
      appendToShadowLog({
        timestamp: new Date().toISOString(),
        session_id: targetId,
        mode: srapResult.contract_mode,
        self_report_detected: true,
        violation: true,
        violation_type: srapResult.violations[0]?.type,
        violation_severity: srapResult.severity,
        confidence: srapResult.confidence_score || 0.9,
        would_block: srapResult.severity === 'ERROR',
        shadow_mode: true,
        llm_response_hash: hashText(proposedResponse)
      });
    }
    
    // Enforced mode: block (Phase C)
    if (SRAP_MODE === 'enforced' && srapResult.severity === 'ERROR') {
      event.context.text = "[Response blocked by self-report policy]";
      event.context._srap_blocked = true;
    }
  }
}
```

### 3. Environment Variables
```bash
# .env or OpenClaw config
SRAP_ENABLED=1
SRAP_MODE=shadow
SRAP_SHADOW_LOG=/home/moonlight/.openclaw/workspace/artifacts/self_report/shadow_log.jsonl
```

### 4. Shadow Log Format
```json
{
  "timestamp": "2026-03-06T00:57:00Z",
  "session_id": "telegram:8420019401",
  "mode": "interpreted",
  "self_report_detected": true,
  "violation": false,
  "violation_type": null,
  "violation_severity": null,
  "allowed_claim_used": true,
  "allowed_claim_text": "当前没有明显愉悦激活",
  "numeric_attempt": false,
  "confidence": 0.92,
  "would_block": false,
  "shadow_mode": true,
  "sampled_for_review": false,
  "llm_response_hash": "a1b2c3d4"
}
```

### 5. Success Criteria
- [ ] self_report_check.py working
- [ ] handler.js integration complete
- [ ] Shadow log being written
- [ ] Environment variables documented
- [ ] Tests passing

## Project Root
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## Test
```bash
# Manual test
python3 emotiond/self_report_check.py "我的joy上升了" emotiond/context.json

# Integration test
node integrations/openclaw/hooks/emotiond-enforcer/handler.js --test
```
