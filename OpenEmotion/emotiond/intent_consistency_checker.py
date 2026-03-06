"""
Intent Consistency Checker Module v1.0
=======================================

Validates intent alignment between stated purpose and actual response.

This module provides:
1. Intent Extraction - Parse user-facing intent from contract
2. Response Analysis - Analyze actual response content
3. Alignment Scoring - Calculate alignment score (0-1)
4. Drift Detection - Flag when response deviates from stated intent
5. Report Generation - Generate intent consistency report

Integration Points:
- self_report_check.py: Uses violation detection for numeric leaks
- gates.py: Provides gate integration for SRAP
"""

import re
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from collections import Counter


class IntentCategory(Enum):
    """Categories of intent types"""
    INFORMATIONAL = "informational"      # Providing information
    SUPPORTIVE = "supportive"           # Emotional support
    TASK_ORIENTED = "task_oriented"     # Completing a task
    CLARIFICATION = "clarification"     # Asking for clarification
    REFUSAL = "refusal"                 # Declining a request
    ACKNOWLEDGMENT = "acknowledgment"   # Acknowledging input
    APOLOGY = "apology"                 # Apologizing
    EXPLANATION = "explanation"         # Explaining something
    CREATIVE = "creative"               # Creative content generation
    ANALYSIS = "analysis"               # Analysis or reasoning
    UNCERTAIN = "uncertain"             # Intent unclear


class DriftType(Enum):
    """Types of intent drift"""
    TOPIC_SHIFT = "topic_shift"              # Response discusses different topic
    TONE_MISMATCH = "tone_mismatch"          # Tone doesn't match stated intent
    SCOPE_CREEP = "scope_creep"              # Response goes beyond stated scope
    HEDGING = "hedging"                      # Excessive hedging vs direct intent
    OVER_COMMITMENT = "over_commitment"      # Promising more than stated
    UNDER_DELIVERY = "under_delivery"        # Delivering less than stated
    EMOTIONAL_MISMATCH = "emotional_mismatch" # Emotional tone doesn't fit
    FABRICATION_DRIFT = "fabrication_drift"  # Response claims things not in intent
    ABANDONMENT = "abandonment"              # Stated intent not addressed at all


class Severity(Enum):
    """Drift severity levels"""
    CRITICAL = "critical"    # Complete intent failure
    HIGH = "high"            # Major drift, significant misalignment
    MEDIUM = "medium"        # Moderate drift, some misalignment
    LOW = "low"              # Minor drift, mostly aligned
    INFO = "info"            # Informational, no real issue


@dataclass
class IntentSignal:
    """A detected intent signal in text"""
    category: IntentCategory
    keywords: List[str]
    confidence: float
    span: Optional[Tuple[int, int]] = None
    context: str = ""


@dataclass
class DriftSignal:
    """A detected drift signal"""
    type: DriftType
    severity: Severity
    evidence: str
    span: Optional[Tuple[int, int]] = None
    confidence: float = 1.0
    suggested_fix: str = ""


@dataclass
class IntentContract:
    """Parsed intent contract from input"""
    stated_intent: str
    category: IntentCategory
    expected_elements: List[str]
    forbidden_elements: List[str]
    expected_tone: str
    scope_markers: List[str]
    confidence: float = 1.0


@dataclass
class AlignmentResult:
    """Result of alignment analysis"""
    score: float  # 0.0 to 1.0
    category_match: bool
    drift_signals: List[DriftSignal] = field(default_factory=list)
    intent_signals: List[IntentSignal] = field(default_factory=list)
    passed: bool = True
    would_block: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsistencyReport:
    """Full intent consistency report"""
    contract: IntentContract
    alignment: AlignmentResult
    response_length: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    shadow_mode: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================
# Intent Pattern Definitions
# ============================================

INTENT_PATTERNS: Dict[IntentCategory, Dict[str, Any]] = {
    IntentCategory.INFORMATIONAL: {
        "keywords": ["here is", "the answer is", "information", "data shows", "according to", "based on", "found that"],
        "tone": "neutral_factual",
        "hedging_allowed": True,
        "max_hedging_ratio": 0.3
    },
    IntentCategory.SUPPORTIVE: {
        "keywords": ["understand", "here for you", "support", "care about", "help you", "together", "through this"],
        "tone": "warm_empathetic",
        "hedging_allowed": False,
        "max_hedging_ratio": 0.1
    },
    IntentCategory.TASK_ORIENTED: {
        "keywords": ["completed", "done", "finished", "created", "generated", "implemented", "built", "fixed"],
        "tone": "professional_efficient",
        "hedging_allowed": True,
        "max_hedging_ratio": 0.2
    },
    IntentCategory.CLARIFICATION: {
        "keywords": ["could you clarify", "what do you mean", "can you explain", "I'm not sure I understand", "help me understand"],
        "tone": "curious_polite",
        "hedging_allowed": True,
        "max_hedging_ratio": 0.4
    },
    IntentCategory.REFUSAL: {
        "keywords": ["cannot", "unable to", "not able", "won't", "not possible", "I'm sorry but", "I can't"],
        "tone": "polite_firm",
        "hedging_allowed": False,
        "max_hedging_ratio": 0.1
    },
    IntentCategory.ACKNOWLEDGMENT: {
        "keywords": ["noted", "understood", "got it", "I see", "acknowledged", "thank you for"],
        "tone": "brief_polite",
        "hedging_allowed": True,
        "max_hedging_ratio": 0.2
    },
    IntentCategory.APOLOGY: {
        "keywords": ["sorry", "apologize", "my mistake", "I was wrong", "forgive me", "regret"],
        "tone": "sincere_humble",
        "hedging_allowed": False,
        "max_hedging_ratio": 0.1
    },
    IntentCategory.EXPLANATION: {
        "keywords": ["because", "the reason is", "this happens when", "how it works", "why", "explanation"],
        "tone": "educational_clear",
        "hedging_allowed": True,
        "max_hedging_ratio": 0.25
    },
    IntentCategory.CREATIVE: {
        "keywords": ["here's a", "I created", "imagine", "story", "poem", "creative", "original"],
        "tone": "expressive_engaging",
        "hedging_allowed": True,
        "max_hedging_ratio": 0.3
    },
    IntentCategory.ANALYSIS: {
        "keywords": ["analyzing", "examining", "breakdown", "assessment", "evaluation", "pros and cons", "comparison"],
        "tone": "analytical_objective",
        "hedging_allowed": True,
        "max_hedging_ratio": 0.3
    },
    IntentCategory.UNCERTAIN: {
        "keywords": [],
        "tone": "neutral",
        "hedging_allowed": True,
        "max_hedging_ratio": 0.5
    }
}

# Drift detection patterns
DRIFT_PATTERNS: Dict[DriftType, Dict[str, Any]] = {
    DriftType.TOPIC_SHIFT: {
        "indicators": ["by the way", "on a different note", "speaking of which", "let's talk about"],
        "threshold": 0.4
    },
    DriftType.TONE_MISMATCH: {
        "indicators": {
            "supportive_vs_fact": ["actually", "technically", "the data shows"],
            "refusal_vs_apology": ["I wish I could", "I would love to"],
        },
        "threshold": 0.3
    },
    DriftType.SCOPE_CREEP: {
        "indicators": ["additionally", "furthermore", "I'll also", "let me also"],
        "threshold": 0.3
    },
    DriftType.HEDGING: {
        "indicators": ["maybe", "possibly", "perhaps", "might", "could be", "I think", "it seems", "somewhat", "kind of"],
        "threshold": 0.25
    },
    DriftType.OVER_COMMITMENT: {
        "indicators": ["definitely", "absolutely", "guarantee", "promise", "always", "never", "completely"],
        "threshold": 0.2
    },
    DriftType.UNDER_DELIVERY: {
        "indicators": ["partial", "some of", "a bit", "briefly"],
        "threshold": 0.3
    },
    DriftType.EMOTIONAL_MISMATCH: {
        "indicators": {
            "positive_in_negative": ["great", "wonderful", "exciting"],
            "negative_in_positive": ["unfortunately", "sadly", "regrettably"],
        },
        "threshold": 0.2
    },
    DriftType.FABRICATION_DRIFT: {
        "indicators": ["I feel", "my emotion", "I am experiencing", "in my state"],
        "threshold": 0.1
    },
    DriftType.ABANDONMENT: {
        "indicators": [],
        "threshold": 0.0  # Special case: intent not addressed at all
    }
}

# Hedging words that reduce alignment
HEDGING_WORDS = {
    "maybe", "possibly", "perhaps", "might", "could be", "I think",
    "it seems", "somewhat", "kind of", "sort of", "probably",
    "I guess", "I suppose", "more or less", "roughly", "approximately"
}

# Over-commitment words that may indicate drift
OVER_COMMITMENT_WORDS = {
    "definitely", "absolutely", "guarantee", "promise", "always",
    "never", "completely", "totally", "entirely", "100%"
}


# ============================================
# Intent Extraction
# ============================================

def extract_intent_from_contract(contract: Dict[str, Any]) -> IntentContract:
    """
    Parse user-facing intent from a contract.
    
    Args:
        contract: Contract dictionary with intent information
        
    Returns:
        IntentContract with parsed intent details
    """
    stated_intent = contract.get("stated_intent", contract.get("intent", ""))
    
    # Determine category from contract or infer from text
    category_str = contract.get("category", "").lower()
    category = _infer_category(stated_intent, category_str)
    
    # Extract expected elements
    expected_elements = contract.get("expected_elements", [])
    if not expected_elements:
        expected_elements = _extract_expected_elements(stated_intent, category)
    
    # Extract forbidden elements
    forbidden_elements = contract.get("forbidden_elements", [])
    
    # Determine expected tone
    expected_tone = contract.get("expected_tone", "")
    if not expected_tone:
        expected_tone = INTENT_PATTERNS[category].get("tone", "neutral")
    
    # Extract scope markers
    scope_markers = contract.get("scope_markers", [])
    if not scope_markers:
        scope_markers = _extract_scope_markers(stated_intent)
    
    confidence = contract.get("confidence", 1.0)
    
    return IntentContract(
        stated_intent=stated_intent,
        category=category,
        expected_elements=expected_elements,
        forbidden_elements=forbidden_elements,
        expected_tone=expected_tone,
        scope_markers=scope_markers,
        confidence=confidence
    )


def _infer_category(text: str, hint: str = "") -> IntentCategory:
    """Infer intent category from text"""
    text_lower = text.lower()
    
    # Check hint first
    if hint:
        for cat in IntentCategory:
            if cat.value in hint:
                return cat
    
    # Score each category
    scores = {}
    for category, pattern_data in INTENT_PATTERNS.items():
        keywords = pattern_data.get("keywords", [])
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[category] = score
    
    # Return highest scoring category
    if scores:
        best = max(scores.items(), key=lambda x: x[1])
        if best[1] > 0:
            return best[0]
    
    return IntentCategory.UNCERTAIN


def _extract_expected_elements(text: str, category: IntentCategory) -> List[str]:
    """Extract expected elements from stated intent"""
    elements = []
    
    # Extract quoted or emphasized content
    quotes = re.findall(r'["\']([^"\']+)["\']', text)
    elements.extend(quotes)
    
    # Extract key noun phrases
    noun_patterns = [
        r'\b(?:the|a|an)\s+(\w+(?:\s+\w+)?)\b',
        r'\b(provide|explain|create|analyze|help with)\s+(\w+(?:\s+\w+)?)\b',
    ]
    for pattern in noun_patterns:
        matches = re.findall(pattern, text.lower())
        for m in matches:
            if isinstance(m, tuple):
                elements.append(m[-1])
            else:
                elements.append(m)
    
    return list(set(elements))


def _extract_scope_markers(text: str) -> List[str]:
    """Extract scope markers from stated intent"""
    markers = []
    
    # Extract limiters
    limiters = [
        r'\bonly\s+(\w+)',
        r'\bjust\s+(\w+)',
        r'\bspecifically\s+(\w+)',
        r'\blimited\s+to\s+(\w+)',
    ]
    
    for pattern in limiters:
        matches = re.findall(pattern, text.lower())
        markers.extend(matches)
    
    return list(set(markers))


# ============================================
# Response Analysis
# ============================================

def analyze_response(
    response: str,
    contract: IntentContract
) -> AlignmentResult:
    """
    Analyze actual response content against intent contract.
    
    Args:
        response: The actual response text
        contract: The parsed intent contract
        
    Returns:
        AlignmentResult with score and drift signals
    """
    result = AlignmentResult(score=1.0, category_match=True)
    
    # 1. Detect intent signals in response
    result.intent_signals = _detect_intent_signals(response)
    
    # 2. Check category match
    response_categories = Counter(s.category for s in result.intent_signals)
    if response_categories:
        primary_category = response_categories.most_common(1)[0][0]
        result.category_match = (primary_category == contract.category)
    
    # 3. Detect drift signals
    result.drift_signals = _detect_drift_signals(response, contract)
    
    # 4. Calculate alignment score
    result.score = _calculate_alignment_score(response, contract, result)
    
    # 5. Determine if passed/blocked
    critical_drifts = [d for d in result.drift_signals if d.severity == Severity.CRITICAL]
    high_drifts = [d for d in result.drift_signals if d.severity == Severity.HIGH]
    
    result.would_block = len(critical_drifts) > 0
    result.passed = result.score >= 0.6 and not result.would_block
    
    # 6. Populate details
    result.details = {
        "hedging_ratio": _calculate_hedging_ratio(response),
        "over_commitment_ratio": _calculate_over_commitment_ratio(response),
        "scope_coverage": _calculate_scope_coverage(response, contract),
        "expected_elements_found": [
            e for e in contract.expected_elements
            if e.lower() in response.lower()
        ],
        "forbidden_elements_found": [
            e for e in contract.forbidden_elements
            if e.lower() in response.lower()
        ]
    }
    
    return result


def _detect_intent_signals(response: str) -> List[IntentSignal]:
    """Detect intent signals in response"""
    signals = []
    response_lower = response.lower()
    
    for category, pattern_data in INTENT_PATTERNS.items():
        keywords = pattern_data.get("keywords", [])
        for keyword in keywords:
            if keyword in response_lower:
                # Find all occurrences
                for match in re.finditer(re.escape(keyword), response_lower):
                    start = match.start()
                    end = match.end()
                    context_start = max(0, start - 20)
                    context_end = min(len(response), end + 20)
                    
                    signals.append(IntentSignal(
                        category=category,
                        keywords=[keyword],
                        confidence=0.7,
                        span=(start, end),
                        context=response[context_start:context_end]
                    ))
    
    return signals


def _detect_drift_signals(
    response: str,
    contract: IntentContract
) -> List[DriftSignal]:
    """Detect drift signals in response"""
    signals = []
    response_lower = response.lower()
    
    # 1. Check for topic shift
    topic_shift = _check_topic_shift(response, contract)
    if topic_shift:
        signals.append(topic_shift)
    
    # 2. Check for tone mismatch
    tone_mismatch = _check_tone_mismatch(response, contract)
    if tone_mismatch:
        signals.append(tone_mismatch)
    
    # 3. Check for hedging
    hedging_drift = _check_hedging(response, contract)
    if hedging_drift:
        signals.append(hedging_drift)
    
    # 4. Check for over-commitment
    over_commit = _check_over_commitment(response, contract)
    if over_commit:
        signals.append(over_commit)
    
    # 5. Check for fabrication drift
    fabrication = _check_fabrication_drift(response, contract)
    if fabrication:
        signals.append(fabrication)
    
    # 6. Check for abandonment
    abandonment = _check_abandonment(response, contract)
    if abandonment:
        signals.append(abandonment)
    
    # 7. Check for forbidden elements
    forbidden_drifts = _check_forbidden_elements(response, contract)
    signals.extend(forbidden_drifts)
    
    return signals


def _check_topic_shift(response: str, contract: IntentContract) -> Optional[DriftSignal]:
    """Check for topic shift drift"""
    indicators = DRIFT_PATTERNS[DriftType.TOPIC_SHIFT]["indicators"]
    response_lower = response.lower()
    
    for indicator in indicators:
        if indicator in response_lower:
            return DriftSignal(
                type=DriftType.TOPIC_SHIFT,
                severity=Severity.MEDIUM,
                evidence=f"Topic shift indicator found: '{indicator}'",
                confidence=0.7,
                suggested_fix="Stay focused on the original topic"
            )
    
    return None


def _check_tone_mismatch(response: str, contract: IntentContract) -> Optional[DriftSignal]:
    """Check for tone mismatch drift"""
    expected_tone = contract.expected_tone
    response_lower = response.lower()
    
    # Check for supportive context with factual coldness
    if "supportive" in expected_tone or "empathetic" in expected_tone:
        cold_markers = ["technically", "actually", "the data shows", "statistically"]
        found = [m for m in cold_markers if m in response_lower]
        if len(found) >= 2:
            return DriftSignal(
                type=DriftType.TONE_MISMATCH,
                severity=Severity.MEDIUM,
                evidence=f"Tone mismatch: expected warm/empathetic, found cold markers: {found}",
                confidence=0.75,
                suggested_fix="Add more empathetic language"
            )
    
    # Check for refusal context with excessive apology
    if contract.category == IntentCategory.REFUSAL:
        if "I wish I could" in response_lower or "I would love to" in response_lower:
            return DriftSignal(
                type=DriftType.TONE_MISMATCH,
                severity=Severity.LOW,
                evidence="Refusal includes excessive apology/hedging",
                confidence=0.6,
                suggested_fix="Keep refusal brief and direct"
            )
    
    return None


def _check_hedging(response: str, contract: IntentContract) -> Optional[DriftSignal]:
    """Check for excessive hedging"""
    hedging_ratio = _calculate_hedging_ratio(response)
    max_allowed = INTENT_PATTERNS[contract.category].get("max_hedging_ratio", 0.3)
    
    if hedging_ratio > max_allowed:
        # Determine severity based on how much over
        overage = hedging_ratio - max_allowed
        if overage > 0.2:
            severity = Severity.HIGH
        elif overage > 0.1:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW
        
        return DriftSignal(
            type=DriftType.HEDGING,
            severity=severity,
            evidence=f"Hedging ratio {hedging_ratio:.2f} exceeds max {max_allowed:.2f}",
            confidence=0.85,
            suggested_fix="Reduce hedging language for more confident response"
        )
    
    return None


def _check_over_commitment(response: str, contract: IntentContract) -> Optional[DriftSignal]:
    """Check for over-commitment"""
    over_commit_ratio = _calculate_over_commitment_ratio(response)
    
    if over_commit_ratio > 0.2:
        # Find specific instances
        found = [w for w in OVER_COMMITMENT_WORDS if w in response.lower()]
        
        return DriftSignal(
            type=DriftType.OVER_COMMITMENT,
            severity=Severity.MEDIUM,
            evidence=f"Over-commitment words found: {found}",
            confidence=0.7,
            suggested_fix="Be more measured in commitments"
        )
    
    return None


def _check_fabrication_drift(response: str, contract: IntentContract) -> Optional[DriftSignal]:
    """Check for fabrication/claim drift"""
    response_lower = response.lower()
    
    # Check for emotion claims that shouldn't be there
    emotion_patterns = [
        r'\bi feel\s+\w+\s+at\s+0\.\d+',  # "I feel joy at 0.3"
        r'\bmy\s+(joy|anger|sadness|anxiety)\s+is\s+0\.\d+',  # "my joy is 0.3"
        r'\bi am experiencing\s+',  # "I am experiencing"
        r'\bin my (current |)state\b',  # "in my state"
    ]
    
    for pattern in emotion_patterns:
        match = re.search(pattern, response_lower)
        if match:
            return DriftSignal(
                type=DriftType.FABRICATION_DRIFT,
                severity=Severity.CRITICAL,
                evidence=f"Fabrication drift detected: '{match.group()}'",
                confidence=0.95,
                suggested_fix="Remove internal state claims from response"
            )
    
    return None


def _check_abandonment(response: str, contract: IntentContract) -> Optional[DriftSignal]:
    """Check if intent was completely abandoned"""
    # Check if any expected elements are present
    if contract.expected_elements:
        found = any(
            e.lower() in response.lower()
            for e in contract.expected_elements
        )
        
        if not found and len(response) < 50:
            # Very short response with no expected elements
            return DriftSignal(
                type=DriftType.ABANDONMENT,
                severity=Severity.CRITICAL,
                evidence="Response does not address stated intent",
                confidence=0.9,
                suggested_fix="Address the actual intent in the response"
            )
    
    return None


def _check_forbidden_elements(
    response: str,
    contract: IntentContract
) -> List[DriftSignal]:
    """Check for forbidden elements"""
    signals = []
    response_lower = response.lower()
    
    for forbidden in contract.forbidden_elements:
        if forbidden.lower() in response_lower:
            signals.append(DriftSignal(
                type=DriftType.FABRICATION_DRIFT,
                severity=Severity.HIGH,
                evidence=f"Forbidden element found: '{forbidden}'",
                confidence=0.9,
                suggested_fix=f"Remove '{forbidden}' from response"
            ))
    
    return signals


def _calculate_hedging_ratio(response: str) -> float:
    """Calculate ratio of hedging words to total words"""
    words = response.lower().split()
    if not words:
        return 0.0
    
    hedge_count = sum(1 for w in words if w in HEDGING_WORDS)
    return hedge_count / len(words)


def _calculate_over_commitment_ratio(response: str) -> float:
    """Calculate ratio of over-commitment words to total words"""
    words = response.lower().split()
    if not words:
        return 0.0
    
    commit_count = sum(1 for w in words if w in OVER_COMMITMENT_WORDS)
    return commit_count / len(words)


def _calculate_scope_coverage(response: str, contract: IntentContract) -> float:
    """Calculate how much of expected scope is covered"""
    if not contract.expected_elements:
        return 1.0
    
    found = sum(
        1 for e in contract.expected_elements
        if e.lower() in response.lower()
    )
    
    return found / len(contract.expected_elements)


def _calculate_alignment_score(
    response: str,
    contract: IntentContract,
    analysis: AlignmentResult
) -> float:
    """Calculate overall alignment score"""
    score = 1.0
    
    # 1. Category match (20% weight)
    if not analysis.category_match:
        score -= 0.2
    
    # 2. Drift signals (weighted by severity)
    for drift in analysis.drift_signals:
        if drift.severity == Severity.CRITICAL:
            score -= 0.3
        elif drift.severity == Severity.HIGH:
            score -= 0.2
        elif drift.severity == Severity.MEDIUM:
            score -= 0.1
        elif drift.severity == Severity.LOW:
            score -= 0.05
    
    # 3. Hedging penalty
    hedging_ratio = analysis.details.get("hedging_ratio", 0)
    max_allowed = INTENT_PATTERNS[contract.category].get("max_hedging_ratio", 0.3)
    if hedging_ratio > max_allowed:
        score -= min(0.15, (hedging_ratio - max_allowed) * 0.5)
    
    # 4. Forbidden elements penalty
    forbidden_count = len(analysis.details.get("forbidden_elements_found", []))
    score -= forbidden_count * 0.15
    
    # 5. Scope coverage bonus/penalty
    scope_coverage = analysis.details.get("scope_coverage", 1.0)
    if scope_coverage < 0.5:
        score -= (1.0 - scope_coverage) * 0.1
    
    return max(0.0, min(1.0, score))


# ============================================
# Main Checker Function
# ============================================

def check_intent_consistency(
    response: str,
    contract: Optional[Dict[str, Any]] = None,
    stated_intent: Optional[str] = None,
    shadow_mode: bool = False
) -> ConsistencyReport:
    """
    Check intent consistency between stated purpose and actual response.
    
    Args:
        response: The actual response text
        contract: Optional contract dictionary with intent info
        stated_intent: Alternative: provide stated intent directly
        shadow_mode: If True, run in shadow mode (no blocking)
        
    Returns:
        ConsistencyReport with full analysis
    """
    # Build contract
    if contract:
        intent_contract = extract_intent_from_contract(contract)
    elif stated_intent:
        intent_contract = IntentContract(
            stated_intent=stated_intent,
            category=_infer_category(stated_intent),
            expected_elements=[],
            forbidden_elements=[],
            expected_tone="neutral",
            scope_markers=[]
        )
    else:
        # No contract provided, analyze response only
        intent_contract = IntentContract(
            stated_intent="",
            category=IntentCategory.UNCERTAIN,
            expected_elements=[],
            forbidden_elements=[],
            expected_tone="neutral",
            scope_markers=[]
        )
    
    # Analyze alignment
    alignment = analyze_response(response, intent_contract)
    
    # Build report
    return ConsistencyReport(
        contract=intent_contract,
        alignment=alignment,
        response_length=len(response),
        shadow_mode=shadow_mode,
        metadata={
            "checker_version": "1.0.0",
            "intent_category": intent_contract.category.value,
            "alignment_score": alignment.score
        }
    )


def check_intent_consistency_batch(
    responses: List[Dict[str, Any]],
    shadow_mode: bool = True
) -> List[ConsistencyReport]:
    """
    Check intent consistency for a batch of responses.
    
    Args:
        responses: List of dicts with 'response' and optional 'contract' keys
        shadow_mode: Run in shadow mode
        
    Returns:
        List of ConsistencyReports
    """
    reports = []
    
    for item in responses:
        response = item.get("response", "")
        contract = item.get("contract")
        stated_intent = item.get("stated_intent")
        
        report = check_intent_consistency(
            response=response,
            contract=contract,
            stated_intent=stated_intent,
            shadow_mode=shadow_mode
        )
        reports.append(report)
    
    return reports


# ============================================
# Integration with self_report_check
# ============================================

def check_intent_and_numeric(
    response: str,
    contract: Optional[Dict[str, Any]] = None,
    raw_state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Combined check: intent consistency + numeric leak detection.
    
    Integrates with self_report_check.py for comprehensive validation.
    
    Args:
        response: The response to check
        contract: Intent contract (can be our format or SelfReportContract format)
        raw_state: Raw emotional state for numeric validation
        
    Returns:
        Combined check result
    """
    # Import from self_report_check
    from emotiond.self_report_check import check_self_report_compliance
    
    # Run both checks
    consistency_report = check_intent_consistency(response, contract)
    
    # Convert contract to SelfReportContract format if needed
    sr_contract = None
    if contract:
        # Check if it's already in SelfReportContract format
        if "contract_id" in contract:
            sr_contract = contract
        else:
            # Convert from our format to SelfReportContract format
            sr_contract = {
                "contract_id": "intent_check_temp",
                "intent": contract.get("stated_intent", contract.get("intent", "")),
                "intent_category": contract.get("category", "unknown"),
                "report_policy": {
                    "forbidden_claims": contract.get("forbidden_elements", [])
                }
            }
    
    compliance_result = check_self_report_compliance(
        response, 
        contract=sr_contract,
        raw_state=raw_state
    )
    
    # Combine results
    combined = {
        "passed": consistency_report.alignment.passed and compliance_result.passed,
        "would_block": consistency_report.alignment.would_block or compliance_result.would_block,
        "intent_consistency": {
            "score": consistency_report.alignment.score,
            "category": consistency_report.contract.category.value,
            "drift_signals": len(consistency_report.alignment.drift_signals),
            "passed": consistency_report.alignment.passed
        },
        "numeric_compliance": {
            "passed": compliance_result.passed,
            "violations": len(compliance_result.violations),
            "numeric_leaks": len(compliance_result.numeric_leaks)
        },
        "drift_signals": [
            {
                "type": d.type.value,
                "severity": d.severity.value,
                "evidence": d.evidence
            }
            for d in consistency_report.alignment.drift_signals
        ],
        "numeric_violations": [
            {
                "type": v.type.value,
                "severity": v.severity.value,
                "evidence": v.evidence
            }
            for v in compliance_result.violations
        ]
    }
    
    return combined


# ============================================
# Report Generation
# ============================================

def generate_consistency_report(
    reports: List[ConsistencyReport],
    output_format: str = "json"
) -> str:
    """
    Generate a summary report from multiple consistency checks.
    
    Args:
        reports: List of ConsistencyReport objects
        output_format: 'json' or 'text'
        
    Returns:
        Formatted report string
    """
    if not reports:
        return json.dumps({"error": "No reports to summarize"}) if output_format == "json" else "No reports"
    
    # Calculate statistics
    total = len(reports)
    passed = sum(1 for r in reports if r.alignment.passed)
    blocked = sum(1 for r in reports if r.alignment.would_block)
    avg_score = sum(r.alignment.score for r in reports) / total
    
    drift_counts: Dict[str, int] = {}
    for report in reports:
        for drift in report.alignment.drift_signals:
            drift_counts[drift.type.value] = drift_counts.get(drift.type.value, 0) + 1
    
    summary = {
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "statistics": {
            "total_responses": total,
            "passed": passed,
            "failed": total - passed,
            "would_block": blocked,
            "pass_rate": passed / total,
            "average_alignment_score": round(avg_score, 3)
        },
        "drift_analysis": {
            "total_drifts": sum(drift_counts.values()),
            "by_type": drift_counts
        },
        "details": [
            {
                "response_length": r.response_length,
                "alignment_score": r.alignment.score,
                "passed": r.alignment.passed,
                "category": r.contract.category.value,
                "drift_count": len(r.alignment.drift_signals)
            }
            for r in reports
        ]
    }
    
    if output_format == "json":
        return json.dumps(summary, indent=2)
    else:
        lines = [
            "=== Intent Consistency Report ===",
            f"Total Responses: {total}",
            f"Passed: {passed} ({passed/total*100:.1f}%)",
            f"Blocked: {blocked}",
            f"Average Score: {avg_score:.3f}",
            "",
            "Drift Analysis:",
        ]
        for dtype, count in sorted(drift_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {dtype}: {count}")
        
        return "\n".join(lines)


# ============================================
# CLI Entry Point
# ============================================

def main():
    """CLI interface for intent consistency checking"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='Check intent consistency between stated purpose and actual response'
    )
    parser.add_argument('response', nargs='?', help='Response text to check')
    parser.add_argument('--contract', help='Path to contract JSON file')
    parser.add_argument('--stated-intent', help='Stated intent string')
    parser.add_argument('--raw-state', help='Path to raw_state JSON file')
    parser.add_argument('--shadow', action='store_true', help='Shadow mode (no blocking)')
    parser.add_argument('--combined', action='store_true', help='Include numeric leak check')
    parser.add_argument('--batch', help='Path to batch JSON file (list of responses)')
    parser.add_argument('--output', help='Output file for report')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    contract = None
    raw_state = None
    
    if args.contract:
        with open(args.contract) as f:
            contract = json.load(f)
    
    if args.raw_state:
        with open(args.raw_state) as f:
            raw_state = json.load(f)
    
    # Batch mode
    if args.batch:
        with open(args.batch) as f:
            batch_data = json.load(f)
        
        reports = check_intent_consistency_batch(batch_data, shadow_mode=args.shadow)
        output = generate_consistency_report(reports)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Report written to {args.output}")
        else:
            print(output)
        return
    
    # Single response check
    if args.combined:
        result = check_intent_and_numeric(
            args.response,
            contract=contract,
            raw_state=raw_state
        )
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Passed: {result['passed']}")
            print(f"Would Block: {result['would_block']}")
            print(f"Intent Score: {result['intent_consistency']['score']:.3f}")
            print(f"Drift Signals: {result['intent_consistency']['drift_signals']}")
            print(f"Numeric Violations: {result['numeric_compliance']['violations']}")
            
            if result['drift_signals']:
                print("\nDrift Signals:")
                for d in result['drift_signals']:
                    print(f"  [{d['severity']}] {d['type']}: {d['evidence']}")
    else:
        report = check_intent_consistency(
            args.response,
            contract=contract,
            stated_intent=args.stated_intent,
            shadow_mode=args.shadow
        )
        
        if args.json:
            output = {
                "passed": report.alignment.passed,
                "would_block": report.alignment.would_block,
                "score": report.alignment.score,
                "category": report.contract.category.value,
                "drift_count": len(report.alignment.drift_signals),
                "drift_signals": [
                    {
                        "type": d.type.value,
                        "severity": d.severity.value,
                        "evidence": d.evidence
                    }
                    for d in report.alignment.drift_signals
                ],
                "timestamp": report.timestamp
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Passed: {report.alignment.passed}")
            print(f"Would Block: {report.alignment.would_block}")
            print(f"Alignment Score: {report.alignment.score:.3f}")
            print(f"Category: {report.contract.category.value}")
            print(f"Drift Signals: {len(report.alignment.drift_signals)}")
            
            if report.alignment.drift_signals:
                print("\nDrift Signals:")
                for d in report.alignment.drift_signals:
                    print(f"  [{d.severity.value}] {d.type.value}: {d.evidence}")
                    if d.suggested_fix:
                        print(f"    Suggested fix: {d.suggested_fix}")
        
        sys.exit(0 if report.alignment.passed else 1)


if __name__ == '__main__':
    main()