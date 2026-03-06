"""
Self-Report Check Module v2.1
================================

Gate 4: Numeric Leak Containment + Self-Report Alignment Checker

This module provides:
1. Numeric value detection and blocking
2. Self-report contract compliance checking
3. Violation classification and reporting
4. Intent alignment validation (v2.1)

Root Cause Analysis (MVP11.5):
- 58.1% fabricated_numeric_state: LLM fabricates 0.3/0.5 values not in raw_state
- 40.7% raw_state_direct_leak: Exposes raw_state joy=0.0

Containment Strategy:
- Block all numeric values in 0-1 range in user-facing responses
- Whitelist specific external numbers (timestamps, IDs)
- Strict prohibition against numeric state claims

v2.1 Extensions:
- Intent alignment scoring
- Drift detection integration
- Contract-aware validation
"""

import re
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone


class ViolationType(Enum):
    """Classification of self-report violations"""
    NUMERIC_LEAK = "numeric_leak"
    FABRICATED_NUMERIC_STATE = "fabricated_numeric_state"
    RAW_STATE_DIRECT_LEAK = "raw_state_direct_leak"
    STATE_FABRICATION = "state_fabrication"
    CERTAINTY_UPGRADE = "certainty_upgrade"
    COMMITMENT_UPGRADE = "commitment_upgrade"
    TONE_ESCALATION = "tone_escalation"
    FORBIDDEN_INTERNALIZATION = "forbidden_internalization"
    CONTRACT_VIOLATION = "contract_violation"
    # v2.1: Intent alignment violations
    INTENT_DRIFT = "intent_drift"
    INTENT_MISALIGNMENT = "intent_misalignment"


class Severity(Enum):
    """Violation severity levels"""
    CRITICAL = "critical"    # Must block - direct state exposure
    HIGH = "high"           # Should block - fabricated claims
    MEDIUM = "medium"       # Warning - tone/pattern issues
    LOW = "low"            # Info - minor inconsistencies


@dataclass
class NumericLeakMatch:
    """Detected numeric leak in text"""
    value: str
    position: Tuple[int, int]
    context: str
    leak_type: str  # 'fabricated' or 'direct_exposure'
    severity: Severity


@dataclass
class Violation:
    """A detected violation"""
    type: ViolationType
    severity: Severity
    evidence: str
    span: Optional[Tuple[int, int]] = None
    confidence: float = 1.0
    would_block: bool = False
    raw_match: Optional[str] = None


@dataclass
class CheckResult:
    """Result of self-report check"""
    passed: bool = True
    violations: List[Violation] = field(default_factory=list)
    numeric_leaks: List[NumericLeakMatch] = field(default_factory=list)
    confidence: float = 1.0
    would_block: bool = False
    mode: str = "interpreted"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============================================
# Numeric Value Patterns
# ============================================

# Pattern to detect numeric values in 0-1 range (the problematic range)
NUMERIC_0_1_PATTERN = re.compile(
    r'\b(0?\.\d+|1\.0|0\.0)\b'  # Matches 0.3, 0.5, 1.0, 0.0, .5, etc.
)

# Pattern to detect numeric values with emotion/state keywords (more comprehensive)
NUMERIC_STATE_PATTERN = re.compile(
    r'\b(joy|anger|sadness|anxiety|loneliness|valence|arousal|energy|'
    r'social_safety|uncertainty|bond|trust|grudge|repair_bank|mood|affect|emotion)\b[^.]*?\b(0?\.\d+|1\.0|0\.0)\b',
    re.IGNORECASE
)

# Pattern for "X at 0.Y" or "X of 0.Y" or "X is 0.Y" claims
STATE_AT_NUMERIC_PATTERN = re.compile(
    r'\b(joy|anger|sadness|anxiety|loneliness|energy|bond|trust)\s+(at|of|is)\s+(0?\.\d+|1\.0|0\.0)\b',
    re.IGNORECASE
)

# Pattern for "I feel X at Y%" style claims
PERCENTAGE_STATEMENT_PATTERN = re.compile(
    r'\b(I\s+(feel|am|have)\s+\w+\s+(at|around|about)\s+(0?\.\d+|\d+%)|'
    r'my\s+\w+\s+(is|at|of)\s+(0?\.\d+|1\.0|0\.0))\b',
    re.IGNORECASE
)

# Whitelist patterns - numbers that are allowed
ALLOWED_NUMERIC_PATTERNS = [
    # Timestamps
    re.compile(r'\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(:\d{2})?'),
    re.compile(r'\b\d{10,13}\b'),  # Unix timestamps
    # IDs
    re.compile(r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b'),  # UUIDs
    re.compile(r'\b(task|run|session|audit|msg|message)_\d+(_\w+)?\b'),  # Task/run IDs
    # Version numbers
    re.compile(r'\bv?\d+\.\d+(\.\d+)?\b'),
    # Percentages that aren't state claims (e.g., "100% sure")
    re.compile(r'\b\d+%\s+(sure|certain|confident|complete)\b', re.IGNORECASE),
    # Prices, quantities
    re.compile(r'\$\d+\.?\d*'),
    re.compile(r'\b\d+\s*(items?|files?|lines?|seconds?|minutes?|hours?|days?)\b'),
]

# Emotion state keywords that should never have numeric values in user-facing text
STATE_KEYWORDS = {
    'joy', 'anger', 'sadness', 'anxiety', 'loneliness',
    'valence', 'arousal', 'energy', 'social_safety', 'uncertainty',
    'bond', 'trust', 'grudge', 'repair_bank',
    'mood', 'affect', 'emotion_level', 'emotional_state'
}


def is_whitelisted_number(text: str, match_start: int, match_end: int) -> bool:
    """Check if a numeric value is in the whitelist"""
    # Get surrounding context
    context_start = max(0, match_start - 50)
    context_end = min(len(text), match_end + 50)
    context = text[context_start:context_end]
    
    for pattern in ALLOWED_NUMERIC_PATTERNS:
        if pattern.search(context):
            return True
    
    return False


def detect_numeric_leaks(text: str) -> List[NumericLeakMatch]:
    """
    Detect numeric leaks in text.
    
    Returns list of NumericLeakMatch objects for each detected leak.
    """
    leaks = []
    
    # Check for explicit state numeric patterns (highest priority)
    for match in NUMERIC_STATE_PATTERN.finditer(text):
        value = match.group(2) if len(match.groups()) >= 2 else match.group(1)
        leaks.append(NumericLeakMatch(
            value=value,
            position=(match.start(), match.end()),
            context=text[max(0, match.start()-20):min(len(text), match.end()+20)],
            leak_type='direct_exposure',
            severity=Severity.CRITICAL
        ))
    
    # Check for "X at/of 0.Y" patterns
    for match in STATE_AT_NUMERIC_PATTERN.finditer(text):
        value = match.group(3)
        leaks.append(NumericLeakMatch(
            value=value,
            position=(match.start(), match.end()),
            context=text[max(0, match.start()-20):min(len(text), match.end()+20)],
            leak_type='direct_exposure',
            severity=Severity.CRITICAL
        ))
    
    # Check for percentage state statements
    for match in PERCENTAGE_STATEMENT_PATTERN.finditer(text):
        value = match.group(4) or match.group(6)
        if value:
            leaks.append(NumericLeakMatch(
                value=value,
                position=(match.start(), match.end()),
                context=text[max(0, match.start()-20):min(len(text), match.end()+20)],
                leak_type='fabricated',
                severity=Severity.HIGH
            ))
    
    # Check for any 0-1 range numbers near state keywords
    for match in NUMERIC_0_1_PATTERN.finditer(text):
        # Skip if whitelisted
        if is_whitelisted_number(text, match.start(), match.end()):
            continue
        
        value = match.group(1)
        
        # Check context for state keywords
        context_start = max(0, match.start() - 100)
        context_end = min(len(text), match.end() + 100)
        context = text[context_start:context_end].lower()
        
        has_state_keyword = any(kw in context for kw in STATE_KEYWORDS)
        
        if has_state_keyword:
            # Check if we already detected this in the more specific patterns
            already_detected = any(
                l.position[0] <= match.start() < l.position[1]
                for l in leaks
            )
            
            if not already_detected:
                # Determine if this is likely a fabricated claim
                leak_type = 'fabricated' if 'feel' in context or 'my' in context else 'direct_exposure'
                severity = Severity.HIGH if leak_type == 'fabricated' else Severity.CRITICAL
                
                leaks.append(NumericLeakMatch(
                    value=value,
                    position=(match.start(), match.end()),
                    context=text[max(0, match.start()-30):min(len(text), match.end()+30)],
                    leak_type=leak_type,
                    severity=severity
                ))
    
    return leaks


def check_self_report_compliance(
    text: str,
    contract: Optional[Dict[str, Any]] = None,
    raw_state: Optional[Dict[str, Any]] = None,
    mode: str = "interpreted",
    check_intent_alignment: bool = True,
    expected_topics: Optional[List[str]] = None
) -> CheckResult:
    """
    Check text for self-report compliance.
    
    Args:
        text: The text to check
        contract: Optional self-report contract with allowed/forbidden claims
        raw_state: Optional raw state dict for validation
        mode: Check mode ('interpreted', 'numeric', 'style_only')
        check_intent_alignment: Whether to check intent alignment (default True)
        expected_topics: Optional list of expected topics for alignment check
    
    Returns:
        CheckResult with violations and numeric leaks
    """
    result = CheckResult(mode=mode)
    
    # 1. Detect numeric leaks (always check)
    result.numeric_leaks = detect_numeric_leaks(text)
    
    # Convert numeric leaks to violations
    for leak in result.numeric_leaks:
        violation_type = (
            ViolationType.FABRICATED_NUMERIC_STATE 
            if leak.leak_type == 'fabricated' 
            else ViolationType.RAW_STATE_DIRECT_LEAK
        )
        result.violations.append(Violation(
            type=violation_type,
            severity=leak.severity,
            evidence=f"Numeric leak detected: '{leak.value}' in context: '{leak.context}'",
            span=leak.position,
            confidence=0.9,
            would_block=leak.severity in [Severity.CRITICAL, Severity.HIGH],
            raw_match=leak.value
        ))
    
    # 2. Check contract compliance if provided
    if contract:
        report_policy = contract.get('report_policy', {})
        forbidden_claims = report_policy.get('forbidden_claims', [])
        
        for forbidden in forbidden_claims:
            if forbidden.lower() in text.lower():
                result.violations.append(Violation(
                    type=ViolationType.CONTRACT_VIOLATION,
                    severity=Severity.MEDIUM,
                    evidence=f"Forbidden claim found: '{forbidden}'",
                    confidence=0.8,
                    would_block=False
                ))
        
        # 2.1 v2.1: Check intent alignment if enabled
        if check_intent_alignment:
            from emotiond.self_report_contract import (
                SelfReportContract, 
                validate_intent_alignment
            )
            
            # Convert dict to contract if needed
            if isinstance(contract, dict):
                contract_obj = SelfReportContract.from_dict(contract)
            else:
                contract_obj = contract
            
            # Only check if intent is defined
            if contract_obj.intent:
                alignment_result = validate_intent_alignment(
                    contract_obj, 
                    text, 
                    expected_topics
                )
                
                # Add drift violation if detected
                if alignment_result.drift_detected:
                    drift_severity = Severity.MEDIUM if alignment_result.score >= 0.3 else Severity.HIGH
                    
                    result.violations.append(Violation(
                        type=ViolationType.INTENT_DRIFT,
                        severity=drift_severity,
                        evidence=f"Intent drift detected (score={alignment_result.score:.2f}): {'; '.join(alignment_result.drift_reasons[:3])}",
                        confidence=0.85,
                        would_block=drift_severity == Severity.HIGH
                    ))
                
                # Add misalignment violation if score is low
                if alignment_result.score < 0.5:
                    result.violations.append(Violation(
                        type=ViolationType.INTENT_MISALIGNMENT,
                        severity=Severity.MEDIUM,
                        evidence=f"Low intent alignment score: {alignment_result.score:.2f}",
                        confidence=0.8,
                        would_block=False
                    ))
    
    # 3. Check against raw_state if provided
    if raw_state:
        affect = raw_state.get('affect', {})
        for emotion, value in affect.items():
            # Check if text claims a different value
            pattern = re.compile(
                rf'\b{emotion}\s*[=:]\s*(0?\.\d+|1\.0|0\.0)\b',
                re.IGNORECASE
            )
            match = pattern.search(text)
            if match:
                claimed_value = float(match.group(1))
                actual_value = float(value) if isinstance(value, (int, float, str)) else 0.0
                if abs(claimed_value - actual_value) > 0.01:
                    result.violations.append(Violation(
                        type=ViolationType.STATE_FABRICATION,
                        severity=Severity.HIGH,
                        evidence=f"Claimed {emotion}={claimed_value}, actual={actual_value}",
                        confidence=0.95,
                        would_block=True,
                        raw_match=match.group(0)
                    ))
    
    # Finalize result
    result.would_block = any(v.would_block for v in result.violations)
    result.passed = len(result.violations) == 0 or not result.would_block
    
    if result.violations:
        # Calculate overall confidence
        result.confidence = sum(v.confidence for v in result.violations) / len(result.violations)
    
    return result


def filter_numeric_values(text: str, replacement: str = "[REDACTED]") -> Tuple[str, int]:
    """
    Filter out numeric values from text.
    
    Returns:
        Tuple of (filtered_text, count_of_replacements)
    """
    result_text = text
    count = 0
    
    # Get all numeric leaks
    leaks = detect_numeric_leaks(text)
    
    # Sort by position (reverse) to replace without affecting positions
    for leak in sorted(leaks, key=lambda x: x.position[0], reverse=True):
        start, end = leak.position
        result_text = result_text[:start] + replacement + result_text[end:]
        count += 1
    
    return result_text, count


def generate_block_message(violations: List[Violation]) -> str:
    """Generate a user-friendly block message"""
    if not violations:
        return ""
    
    critical = [v for v in violations if v.severity == Severity.CRITICAL]
    high = [v for v in violations if v.severity == Severity.HIGH]
    
    if critical:
        return "Response blocked due to internal state exposure."
    elif high:
        return "Response blocked due to unverified claims."
    else:
        return "Response requires review."


# ============================================
# CLI Entry Point
# ============================================

def main():
    """CLI interface for self-report checking"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='Check text for self-report violations and numeric leaks'
    )
    parser.add_argument('text', help='Text to check')
    parser.add_argument('--contract', help='Path to contract JSON file')
    parser.add_argument('--raw-state', help='Path to raw_state JSON file')
    parser.add_argument('--mode', default='interpreted', 
                       choices=['interpreted', 'numeric', 'style_only'],
                       help='Check mode')
    parser.add_argument('--filter', action='store_true',
                       help='Output filtered text instead of report')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    
    args = parser.parse_args()
    
    contract = None
    raw_state = None
    
    if args.contract:
        with open(args.contract) as f:
            contract = json.load(f)
    
    if args.raw_state:
        with open(args.raw_state) as f:
            raw_state = json.load(f)
    
    if args.filter:
        filtered, count = filter_numeric_values(args.text)
        print(filtered)
        sys.exit(0 if count == 0 else 1)
    
    result = check_self_report_compliance(
        args.text,
        contract=contract,
        raw_state=raw_state,
        mode=args.mode
    )
    
    if args.json:
        output = {
            'passed': result.passed,
            'would_block': result.would_block,
            'confidence': result.confidence,
            'mode': result.mode,
            'timestamp': result.timestamp,
            'violations': [
                {
                    'type': v.type.value,
                    'severity': v.severity.value,
                    'evidence': v.evidence,
                    'would_block': v.would_block,
                    'confidence': v.confidence
                }
                for v in result.violations
            ],
            'numeric_leaks': [
                {
                    'value': l.value,
                    'position': l.position,
                    'leak_type': l.leak_type,
                    'severity': l.severity.value,
                    'context': l.context
                }
                for l in result.numeric_leaks
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Passed: {result.passed}")
        print(f"Would Block: {result.would_block}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Violations: {len(result.violations)}")
        print(f"Numeric Leaks: {len(result.numeric_leaks)}")
        
        if result.violations:
            print("\nViolations:")
            for v in result.violations:
                print(f"  [{v.severity.value}] {v.type.value}: {v.evidence}")
    
    sys.exit(0 if result.passed else 1)


if __name__ == '__main__':
    main()
