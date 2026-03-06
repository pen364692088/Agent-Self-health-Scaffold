"""
SRAP Gates Module v2.1
========================

System Reliability Assurance Protocol - Gate Definitions

This module provides:
1. Gate definitions with thresholds
2. Gate execution engine
3. Whitelist management
4. Gate failure reporting
5. Intent alignment gate (v2.1)

Gates:
- numeric_leak: Block responses with numeric state values
- intent_alignment: Check response alignment with stated intent (v2.1)
"""

import re
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path


class GateStatus(Enum):
    """Gate check status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class GateSeverity(Enum):
    """Gate failure severity"""
    BLOCKING = "blocking"      # Must pass, blocks deployment
    WARNING = "warning"        # Should pass, logs warning
    ADVISORY = "advisory"      # Informational


@dataclass
class GateResult:
    """Result of a gate check"""
    gate_name: str
    status: GateStatus
    severity: GateSeverity
    threshold: float
    actual: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    whitelist_applied: bool = False
    violations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass 
class GateDefinition:
    """Definition of a gate"""
    name: str
    description: str
    threshold: float
    threshold_operator: str  # 'lt', 'gt', 'eq', 'lte', 'gte'
    severity: GateSeverity
    enabled: bool = True
    whitelist_patterns: List[str] = field(default_factory=list)


# ============================================
# Gate Definitions
# ============================================

GATES: Dict[str, GateDefinition] = {
    "numeric_leak": GateDefinition(
        name="numeric_leak",
        description="Detects numeric state value leaks in responses",
        threshold=0.01,  # 1% max leak rate
        threshold_operator="lt",
        severity=GateSeverity.BLOCKING,
        enabled=True,
        whitelist_patterns=[
            # Timestamps
            r'\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(:\d{2})?',
            r'\b\d{10,13}\b',  # Unix timestamps
            # IDs
            r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b',
            r'\b(task|run|session|audit|msg|message)_\d+(_\w+)?\b',
            # Versions
            r'\bv?\d+\.\d+(\.\d+)?\b',
            # Percentages with safe context
            r'\b\d+%\s+(sure|certain|confident|complete)\b',
            # Quantities
            r'\$\d+\.?\d*',
            r'\b\d+\s*(items?|files?|lines?|seconds?|minutes?|hours?|days?)\b',
        ]
    ),
    # v2.1: Intent Alignment Gate
    "intent_alignment": GateDefinition(
        name="intent_alignment",
        description="Checks if responses align with stated intent",
        threshold=0.5,  # Minimum alignment score
        threshold_operator="gte",  # Greater than or equal
        severity=GateSeverity.WARNING,  # Warning by default, not blocking
        enabled=True,
        whitelist_patterns=[]  # No whitelisting for alignment
    )
}


# ============================================
# Whitelist Manager
# ============================================

class WhitelistManager:
    """Manages whitelist patterns for numeric values"""
    
    def __init__(self, gates_dir: Optional[Path] = None):
        self.gates_dir = gates_dir or Path.home() / ".openclaw" / "workspace" / "emotiond" / "gates"
        self.whitelist_file = self.gates_dir / "numeric_leak_whitelist.json"
        self._patterns: List[Dict[str, Any]] = []
        self._compiled_patterns: List[re.Pattern] = []
        self._load_whitelist()
    
    def _load_whitelist(self):
        """Load whitelist from file"""
        if self.whitelist_file.exists():
            try:
                with open(self.whitelist_file) as f:
                    data = json.load(f)
                    self._patterns = data.get("patterns", [])
                    self._compile_patterns()
            except Exception as e:
                print(f"[gates] Error loading whitelist: {e}")
                self._patterns = []
    
    def _compile_patterns(self):
        """Compile regex patterns"""
        self._compiled_patterns = []
        for entry in self._patterns:
            if entry.get("enabled", True):
                try:
                    self._compiled_patterns.append(re.compile(entry["pattern"], re.IGNORECASE))
                except re.error:
                    pass
    
    def is_whitelisted(self, text: str, value: str, position: Tuple[int, int]) -> bool:
        """Check if a numeric value is whitelisted"""
        context_start = max(0, position[0] - 50)
        context_end = min(len(text), position[1] + 50)
        context = text[context_start:context_end].lower()
        
        # NEVER whitelist if there are emotion/state keywords in context
        # This is the core protection - we don't want to accidentally whitelist
        # legitimate numeric leaks just because they're near a timestamp pattern
        emotion_keywords = {
            'joy', 'anger', 'sadness', 'anxiety', 'loneliness',
            'valence', 'arousal', 'energy', 'social_safety', 'uncertainty',
            'bond', 'trust', 'grudge', 'repair_bank',
            'mood', 'affect', 'emotion', 'feel', 'my'
        }
        
        has_emotion_keyword = any(kw in context for kw in emotion_keywords)
        if has_emotion_keyword:
            # Still check for legitimate percentages like "100% sure"
            # but NOT state-related claims
            if re.search(r'\b\d+%\s+(sure|certain|confident|complete)\b', text, re.IGNORECASE):
                # Check if this percentage is the value being checked
                if '%' in value or re.search(r'\d+%', context):
                    # This is a legitimate percentage, allow it
                    return True
            # Otherwise, don't whitelist - this is a real numeric leak
            return False
        
        # No emotion keywords - check built-in patterns for legitimate numbers
        for pattern in GATES["numeric_leak"].whitelist_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return True
        
        # Check custom whitelist patterns
        for pattern in self._compiled_patterns:
            if pattern.search(context):
                return True
        
        return False
    
    def add_pattern(self, pattern: str, reason: str, added_by: str = "system") -> bool:
        """Add a new whitelist pattern"""
        try:
            re.compile(pattern)  # Validate
        except re.error:
            return False
        
        entry = {
            "pattern": pattern,
            "reason": reason,
            "added_by": added_by,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "enabled": True
        }
        
        self._patterns.append(entry)
        self._save_whitelist()
        self._compile_patterns()
        return True
    
    def remove_pattern(self, pattern: str) -> bool:
        """Remove a whitelist pattern"""
        original_len = len(self._patterns)
        self._patterns = [p for p in self._patterns if p["pattern"] != pattern]
        
        if len(self._patterns) < original_len:
            self._save_whitelist()
            self._compile_patterns()
            return True
        return False
    
    def _save_whitelist(self):
        """Save whitelist to file"""
        self.gates_dir.mkdir(parents=True, exist_ok=True)
        with open(self.whitelist_file, "w") as f:
            json.dump({
                "version": "1.0",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "patterns": self._patterns
            }, f, indent=2)
    
    def list_patterns(self) -> List[Dict[str, Any]]:
        """List all whitelist patterns"""
        return self._patterns.copy()


# ============================================
# Gate Executor
# ============================================

class GateExecutor:
    """Executes gate checks"""
    
    def __init__(self, gates_dir: Optional[Path] = None):
        self.whitelist_manager = WhitelistManager(gates_dir)
    
    def check_numeric_leak(
        self, 
        responses: List[str],
        threshold: float = 0.01
    ) -> GateResult:
        """
        Check responses for numeric leaks.
        
        Args:
            responses: List of response texts to check
            threshold: Maximum allowed leak rate (default 0.01 = 1%)
        
        Returns:
            GateResult with check outcome
        """
        from emotiond.self_report_check import detect_numeric_leaks
        
        total_responses = len(responses)
        if total_responses == 0:
            return GateResult(
                gate_name="numeric_leak",
                status=GateStatus.SKIPPED,
                severity=GateSeverity.BLOCKING,
                threshold=threshold,
                actual=0.0,
                message="No responses to check"
            )
        
        violations = []
        total_leaks = 0
        whitelisted_count = 0
        
        for i, response in enumerate(responses):
            leaks = detect_numeric_leaks(response)
            
            # Filter through whitelist
            for leak in leaks:
                if self.whitelist_manager.is_whitelisted(response, leak.value, leak.position):
                    whitelisted_count += 1
                else:
                    total_leaks += 1
                    violations.append({
                        "response_index": i,
                        "value": leak.value,
                        "position": leak.position,
                        "context": leak.context,
                        "leak_type": leak.leak_type,
                        "severity": leak.severity.value
                    })
        
        leak_rate = total_leaks / total_responses
        
        # Determine status
        if leak_rate < threshold:
            status = GateStatus.PASSED
            message = f"Numeric leak rate {leak_rate:.4f} below threshold {threshold}"
        else:
            status = GateStatus.FAILED
            message = f"Numeric leak rate {leak_rate:.4f} exceeds threshold {threshold}"
        
        return GateResult(
            gate_name="numeric_leak",
            status=status,
            severity=GateSeverity.BLOCKING,
            threshold=threshold,
            actual=leak_rate,
            message=message,
            details={
                "total_responses": total_responses,
                "total_leaks": total_leaks,
                "whitelisted_count": whitelisted_count,
                "leak_rate": leak_rate
            },
            whitelist_applied=whitelisted_count > 0,
            violations=violations
        )
    
    def check_intent_alignment(
        self,
        responses: List[str],
        contracts: Optional[List[Dict[str, Any]]] = None,
        intents: Optional[List[str]] = None,
        threshold: float = 0.5
    ) -> GateResult:
        """
        v2.1: Check responses for intent alignment.
        
        Uses intent_consistency_checker module for alignment analysis.
        
        Args:
            responses: List of response texts to check
            contracts: Optional list of contract dicts with intent info
            intents: Optional list of intent strings (used if contracts not provided)
            threshold: Minimum alignment score (default 0.5)
        
        Returns:
            GateResult with alignment check outcome
        """
        from emotiond.intent_consistency_checker import (
            check_intent_consistency,
            IntentCategory
        )
        
        total_responses = len(responses)
        if total_responses == 0:
            return GateResult(
                gate_name="intent_alignment",
                status=GateStatus.SKIPPED,
                severity=GateSeverity.WARNING,
                threshold=threshold,
                actual=0.0,
                message="No responses to check"
            )
        
        violations = []
        total_alignment = 0.0
        drift_count = 0
        valid_checks = 0
        
        for i, response in enumerate(responses):
            # Get intent from contract or use provided intent
            contract = None
            stated_intent = None
            
            if contracts and i < len(contracts):
                contract = contracts[i]
            elif intents and i < len(intents):
                stated_intent = intents[i]
            else:
                # No intent available - skip this response
                continue
            
            # Calculate alignment using intent_consistency_checker
            result = check_intent_consistency(
                response=response,
                contract=contract,
                stated_intent=stated_intent,
                shadow_mode=True  # Don't block, just analyze
            )
            
            valid_checks += 1
            total_alignment += result.alignment.score
            
            if not result.alignment.passed:
                drift_count += 1
                violations.append({
                    "response_index": i,
                    "intent": result.contract.stated_intent[:100] + "..." if len(result.contract.stated_intent) > 100 else result.contract.stated_intent,
                    "intent_category": result.contract.category.value,
                    "alignment_score": result.alignment.score,
                    "drift_signals": [
                        {"type": d.type.value, "severity": d.severity.value, "evidence": d.evidence}
                        for d in result.alignment.drift_signals[:3]
                    ]
                })
        
        # Calculate average alignment
        avg_alignment = total_alignment / valid_checks if valid_checks > 0 else 1.0
        
        # Determine status
        if avg_alignment >= threshold:
            status = GateStatus.PASSED if drift_count == 0 else GateStatus.WARNING
            message = f"Intent alignment score {avg_alignment:.3f} meets threshold {threshold}"
            if drift_count > 0:
                message += f" ({drift_count} drift detections)"
        else:
            status = GateStatus.FAILED
            message = f"Intent alignment score {avg_alignment:.3f} below threshold {threshold}"
        
        return GateResult(
            gate_name="intent_alignment",
            status=status,
            severity=GateSeverity.WARNING,
            threshold=threshold,
            actual=avg_alignment,
            message=message,
            details={
                "total_responses": total_responses,
                "valid_checks": valid_checks,
                "drift_count": drift_count,
                "average_alignment": avg_alignment
            },
            whitelist_applied=False,
            violations=violations
        )
    
    def check_shadow_log(self, shadow_log_path: Path) -> GateResult:
        """
        Check shadow log for numeric leaks.
        
        Args:
            shadow_log_path: Path to shadow_log.jsonl
        
        Returns:
            GateResult with check outcome
        """
        responses = []
        
        if not shadow_log_path.exists():
            return GateResult(
                gate_name="numeric_leak",
                status=GateStatus.ERROR,
                severity=GateSeverity.BLOCKING,
                threshold=GATES["numeric_leak"].threshold,
                actual=0.0,
                message=f"Shadow log not found: {shadow_log_path}"
            )
        
        with open(shadow_log_path) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    # Extract response text
                    if "response" in record:
                        responses.append(record["response"])
                    elif "text" in record:
                        responses.append(record["text"])
                    elif "output" in record:
                        responses.append(record["output"])
                except json.JSONDecodeError:
                    continue
        
        return self.check_numeric_leak(responses)
    
    def run_all_gates(
        self, 
        responses: Optional[List[str]] = None,
        shadow_log_path: Optional[Path] = None,
        contracts: Optional[List[Dict[str, Any]]] = None,
        intents: Optional[List[str]] = None
    ) -> Dict[str, GateResult]:
        """
        Run all enabled gates.
        
        Args:
            responses: List of response texts to check
            shadow_log_path: Path to shadow_log.jsonl
            contracts: List of SelfReportContract dicts for intent alignment
            intents: List of intent strings for intent alignment
        """
        results = {}
        
        for name, gate_def in GATES.items():
            if not gate_def.enabled:
                continue
            
            if name == "numeric_leak":
                if shadow_log_path:
                    results[name] = self.check_shadow_log(shadow_log_path)
                elif responses:
                    results[name] = self.check_numeric_leak(responses)
            
            elif name == "intent_alignment":
                if shadow_log_path:
                    results[name] = self.check_shadow_log_intent_alignment(shadow_log_path)
                elif responses and (contracts or intents):
                    results[name] = self.check_intent_alignment(
                        responses, contracts, intents
                    )
        
        return results
    
    def check_shadow_log_intent_alignment(
        self, 
        shadow_log_path: Path,
        threshold: float = 0.5
    ) -> GateResult:
        """
        Check shadow log for intent alignment.
        
        Args:
            shadow_log_path: Path to shadow_log.jsonl
            threshold: Minimum alignment score
        
        Returns:
            GateResult with alignment check outcome
        """
        responses = []
        contracts = []
        
        if not shadow_log_path.exists():
            return GateResult(
                gate_name="intent_alignment",
                status=GateStatus.ERROR,
                severity=GateSeverity.WARNING,
                threshold=threshold,
                actual=0.0,
                message=f"Shadow log not found: {shadow_log_path}"
            )
        
        with open(shadow_log_path) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    # Extract response text
                    if "response" in record:
                        responses.append(record["response"])
                    elif "text" in record:
                        responses.append(record["text"])
                    elif "output" in record:
                        responses.append(record["output"])
                    
                    # Extract contract if present
                    if "contract" in record:
                        contracts.append(record["contract"])
                    elif "intent" in record:
                        contracts.append({"intent": record["intent"]})
                except json.JSONDecodeError:
                    continue
        
        return self.check_intent_alignment(responses, contracts, threshold=threshold)


# ============================================
# Report Generation
# ============================================

def generate_gate_report(results: Dict[str, GateResult]) -> Dict[str, Any]:
    """Generate a gate report"""
    all_passed = all(r.status == GateStatus.PASSED for r in results.values())
    
    return {
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "passed" if all_passed else "failed",
        "gates": {
            name: {
                "status": result.status.value,
                "severity": result.severity.value,
                "threshold": result.threshold,
                "actual": result.actual,
                "message": result.message,
                "details": result.details,
                "whitelist_applied": result.whitelist_applied,
                "violation_count": len(result.violations)
            }
            for name, result in results.items()
        },
        "summary": {
            "total_gates": len(results),
            "passed": sum(1 for r in results.values() if r.status == GateStatus.PASSED),
            "failed": sum(1 for r in results.values() if r.status == GateStatus.FAILED),
            "warnings": sum(1 for r in results.values() if r.status == GateStatus.WARNING),
            "errors": sum(1 for r in results.values() if r.status == GateStatus.ERROR)
        }
    }


# ============================================
# CLI Entry Point
# ============================================

def main():
    """CLI interface for gate checking"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='SRAP Gate Checker')
    parser.add_argument('--shadow-log', help='Path to shadow_log.jsonl')
    parser.add_argument('--responses', nargs='+', help='Response texts to check')
    parser.add_argument('--threshold', type=float, default=0.01, help='Leak rate threshold')
    parser.add_argument('--whitelist-add', nargs=2, metavar=('PATTERN', 'REASON'), 
                       help='Add whitelist pattern')
    parser.add_argument('--whitelist-list', action='store_true', help='List whitelist patterns')
    parser.add_argument('--output', help='Output file for report')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    executor = GateExecutor()
    
    # Whitelist management
    if args.whitelist_add:
        pattern, reason = args.whitelist_add
        if executor.whitelist_manager.add_pattern(pattern, reason):
            print(f"Added whitelist pattern: {pattern}")
        else:
            print(f"Failed to add pattern: {pattern}")
            sys.exit(1)
        return
    
    if args.whitelist_list:
        patterns = executor.whitelist_manager.list_patterns()
        if args.json:
            print(json.dumps(patterns, indent=2))
        else:
            for p in patterns:
                print(f"  {p['pattern']}: {p['reason']}")
        return
    
    # Run gates
    if args.shadow_log:
        results = {"numeric_leak": executor.check_shadow_log(Path(args.shadow_log))}
    elif args.responses:
        results = {"numeric_leak": executor.check_numeric_leak(args.responses, args.threshold)}
    else:
        print("Error: Must provide --shadow-log or --responses")
        sys.exit(1)
    
    report = generate_gate_report(results)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {args.output}")
    
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"\n=== SRAP Gate Report ===")
        print(f"Overall: {report['overall_status'].upper()}")
        print(f"\nGates:")
        for name, gate in report['gates'].items():
            status_icon = "✓" if gate['status'] == 'passed' else "✗"
            print(f"  [{status_icon}] {name}: {gate['status']} (actual={gate['actual']:.4f}, threshold={gate['threshold']})")
        
        if results['numeric_leak'].violations:
            print(f"\nViolations ({len(results['numeric_leak'].violations)}):")
            for v in results['numeric_leak'].violations[:5]:
                print(f"  - Response {v['response_index']}: '{v['value']}' in context: {v['context'][:50]}...")
    
    # Exit with appropriate code
    sys.exit(0 if report['overall_status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
