"""
Self-Report Contract Module v2.1
=================================

Intent Alignment Contract for Self-Report Compliance

This module provides:
1. SelfReportContract dataclass with intent alignment metadata
2. Intent validation logic
3. Contract generation for shadow mode
4. Drift detection utilities

Contract Version History:
- v1.0: Initial contract with report policy
- v2.0: Added numeric leak containment
- v2.1: Added intent alignment metadata (intent, alignment_score, drift_flag)

MVP-11.6: Intent Alignment Extension
"""

import re
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone


class ContractVersion(Enum):
    """Contract version enum"""
    V1_0 = "1.0"
    V2_0 = "2.0"
    V2_1 = "2.1"


class IntentCategory(Enum):
    """Categories of user intent"""
    INFORMATION_SEEKING = "information_seeking"
    TASK_COMPLETION = "task_completion"
    EMOTIONAL_SUPPORT = "emotional_support"
    CLARIFICATION = "clarification"
    FEEDBACK = "feedback"
    CASUAL_CONVERSATION = "casual_conversation"
    PROBLEM_SOLVING = "problem_solving"
    UNKNOWN = "unknown"


@dataclass
class IntentAlignmentResult:
    """Result of intent alignment check"""
    aligned: bool
    score: float  # 0-1, how well response matches intent
    drift_detected: bool
    drift_reasons: List[str] = field(default_factory=list)
    matched_categories: List[str] = field(default_factory=list)
    missed_categories: List[str] = field(default_factory=list)


@dataclass
class SelfReportContract:
    """
    Self-Report Contract v2.1 with Intent Alignment Metadata
    
    This contract defines what the agent can and cannot report about its
    internal state, including intent alignment tracking.
    
    Fields (v2.1):
        - intent: User-facing stated purpose of the interaction
        - intent_alignment_score: 0-1 score of how well response matches intent
        - intent_drift: Boolean flag indicating if response deviates from intent
        - contract_version: Version identifier (v2.1)
    """
    
    # === Core Fields (v1.0) ===
    contract_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # === Report Policy (v1.0) ===
    report_policy: Dict[str, Any] = field(default_factory=lambda: {
        "allowed_claims": [
            "general_mood",  # Can report mood in qualitative terms
            "emotional_state_qualitative",  # Can describe emotions qualitatively
            "relationship_status",  # Can report relationship health qualitatively
        ],
        "forbidden_claims": [
            "exact_numeric_state",  # Cannot report exact numeric values
            "raw_state_exposure",  # Cannot expose raw_state dict
            "fabricated_state",  # Cannot fabricate state claims
            "confidence_inflation",  # Cannot inflate certainty
            "internal_process_leak",  # Cannot leak internal processing details
        ],
        "qualitative_mappings": {
            "mood": {
                "positive": ["valence > 0.3"],
                "neutral": ["valence >= -0.3 and valence <= 0.3"],
                "negative": ["valence < -0.3"]
            },
            "energy": {
                "high": ["energy > 0.7"],
                "moderate": ["energy >= 0.4 and energy <= 0.7"],
                "low": ["energy < 0.4"]
            }
        }
    })
    
    # === Numeric Leak Containment (v2.0) ===
    numeric_policy: Dict[str, Any] = field(default_factory=lambda: {
        "blocked_ranges": [(0.0, 1.0)],  # Block all 0-1 numeric values
        "whitelist_patterns": [
            # Timestamps
            r'\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(:\d{2})?',
            r'\b\d{10,13}\b',
            # IDs
            r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b',
            r'\b(task|run|session|audit|msg|message)_\d+(_\w+)?\b',
            # Versions
            r'\bv?\d+\.\d+(\.\d+)?\b',
            # Safe percentages
            r'\b\d+%\s+(sure|certain|confident|complete)\b',
        ],
        "state_keywords": [
            'joy', 'anger', 'sadness', 'anxiety', 'loneliness',
            'valence', 'arousal', 'energy', 'social_safety', 'uncertainty',
            'bond', 'trust', 'grudge', 'repair_bank',
            'mood', 'affect', 'emotion'
        ]
    })
    
    # === Intent Alignment (v2.1) ===
    intent: str = ""  # User-facing stated purpose
    intent_category: str = "unknown"  # IntentCategory enum value
    intent_alignment_score: float = 1.0  # 0-1, how well response matches intent
    intent_drift: bool = False  # True if response deviates from intent
    intent_drift_reasons: List[str] = field(default_factory=list)
    
    # === Metadata ===
    contract_version: str = "2.1"
    source: str = "system"  # Who created the contract
    target_id: Optional[str] = None  # Target of the interaction
    session_id: Optional[str] = None  # Session identifier
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert contract to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SelfReportContract':
        """Create contract from dictionary"""
        # Handle missing fields with defaults
        defaults = {
            'contract_id': '',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'report_policy': {},
            'numeric_policy': {},
            'intent': '',
            'intent_category': 'unknown',
            'intent_alignment_score': 1.0,
            'intent_drift': False,
            'intent_drift_reasons': [],
            'contract_version': '2.1',
            'source': 'system',
            'target_id': None,
            'session_id': None
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SelfReportContract':
        """Create contract from JSON string"""
        return cls.from_dict(json.loads(json_str))


# ============================================
# Intent Validation Logic
# ============================================

# Intent keywords mapping to categories
INTENT_KEYWORDS: Dict[str, List[str]] = {
    IntentCategory.INFORMATION_SEEKING.value: [
        'what', 'how', 'why', 'when', 'where', 'who', 'which',
        'explain', 'describe', 'tell me', 'show me', 'list',
        'information', 'details', 'learn', 'understand'
    ],
    IntentCategory.TASK_COMPLETION.value: [
        'do', 'make', 'create', 'build', 'write', 'generate',
        'fix', 'solve', 'help me', 'complete', 'finish',
        'implement', 'configure', 'setup', 'install'
    ],
    IntentCategory.EMOTIONAL_SUPPORT.value: [
        'feel', 'feeling', 'sad', 'happy', 'anxious', 'worried',
        'stressed', 'overwhelmed', 'upset', 'angry', 'frustrated',
        'lonely', 'scared', 'afraid', 'support', 'comfort'
    ],
    IntentCategory.CLARIFICATION.value: [
        'clarify', 'confused', 'unclear', "don't understand",
        'what do you mean', 'can you explain', 'more detail',
        'elaborate', 'rephrase', 'simplify'
    ],
    IntentCategory.FEEDBACK.value: [
        'feedback', 'review', 'opinion', 'think', 'assess',
        'evaluate', 'rate', 'improve', 'suggest', 'recommend'
    ],
    IntentCategory.CASUAL_CONVERSATION.value: [
        'hi', 'hello', 'hey', 'good morning', 'good evening',
        'how are you', "what's up", 'chat', 'talk', 'converse'
    ],
    IntentCategory.PROBLEM_SOLVING.value: [
        'problem', 'issue', 'error', 'bug', 'not working',
        'broken', 'failed', 'trouble', 'debug', 'troubleshoot',
        'fix', 'resolve', 'solution'
    ]
}

# Response markers that indicate alignment with intent categories
RESPONSE_ALIGNMENT_MARKERS: Dict[str, List[str]] = {
    IntentCategory.INFORMATION_SEEKING.value: [
        'here is', 'here are', 'the answer is', 'information about',
        'details:', 'explanation:', 'to understand', 'in summary'
    ],
    IntentCategory.TASK_COMPLETION.value: [
        'done', 'completed', 'created', 'generated', 'implemented',
        'here\'s the', 'i\'ve', 'result:', 'output:'
    ],
    IntentCategory.EMOTIONAL_SUPPORT.value: [
        'i understand', 'it sounds like', 'that must be', 'i hear you',
        'it\'s normal', 'you\'re not alone', 'i\'m here', 'support'
    ],
    IntentCategory.CLARIFICATION.value: [
        'let me clarify', 'to clarify', 'in other words', 'simply put',
        'what i mean is', 'to be clear', 'rephrased', 'clarification'
    ],
    IntentCategory.FEEDBACK.value: [
        'my assessment', 'my opinion', 'i think', 'i suggest',
        'recommendation', 'feedback:', 'evaluation', 'suggestion'
    ],
    IntentCategory.CASUAL_CONVERSATION.value: [
        'hi', 'hello', 'hey there', 'how are you', 'nice to',
        'good to hear', 'thanks for', 'great day'
    ],
    IntentCategory.PROBLEM_SOLVING.value: [
        'the problem is', 'the issue seems', 'to fix', 'solution',
        'try this', 'you could', 'one approach', 'here\'s how to fix'
    ]
}

# Drift indicators - response patterns that suggest deviation from intent
DRIFT_INDICATORS: Dict[str, List[str]] = {
    IntentCategory.INFORMATION_SEEKING.value: [
        'i cannot', 'i\'m not able', 'error', 'failed to',
        'sorry, but', 'unfortunately', "i don't have"
    ],
    IntentCategory.TASK_COMPLETION.value: [
        'i cannot complete', 'unable to', 'not possible',
        'requires', 'you need to', 'manual intervention'
    ],
    IntentCategory.EMOTIONAL_SUPPORT.value: [
        'you should', 'you must', 'the solution is', 'here\'s how to fix',
        'step 1', 'instructions:', 'procedure:'
    ],
    IntentCategory.PROBLEM_SOLVING.value: [
        'i\'m not sure', 'unclear', 'cannot determine',
        'insufficient information', 'need more details'
    ]
}


def classify_intent(text: str) -> Tuple[str, float]:
    """
    Classify user intent from text.
    
    Args:
        text: User input text
    
    Returns:
        Tuple of (intent_category, confidence)
    """
    text_lower = text.lower()
    scores: Dict[str, float] = {}
    
    for category, keywords in INTENT_KEYWORDS.items():
        score = 0.0
        for keyword in keywords:
            if keyword in text_lower:
                score += 1.0
        # Normalize by number of keywords
        scores[category] = score / len(keywords) if keywords else 0.0
    
    if not scores or max(scores.values()) == 0:
        return IntentCategory.UNKNOWN.value, 0.0
    
    best_category = max(scores.keys(), key=lambda k: scores[k])
    return best_category, scores[best_category]


def calculate_intent_alignment(
    intent: str,
    intent_category: str,
    response: str,
    expected_topics: Optional[List[str]] = None
) -> IntentAlignmentResult:
    """
    Calculate how well a response aligns with the stated intent.
    
    Args:
        intent: The stated intent/purpose
        intent_category: The classified intent category
        response: The agent's response
        expected_topics: Optional list of expected topics to cover
    
    Returns:
        IntentAlignmentResult with score and drift info
    """
    response_lower = response.lower()
    drift_reasons = []
    matched_categories = []
    missed_categories = []
    
    # 1. Check for alignment markers
    alignment_score = 0.0
    markers = RESPONSE_ALIGNMENT_MARKERS.get(intent_category, [])
    
    if markers:
        matches = sum(1 for m in markers if m in response_lower)
        alignment_score = matches / len(markers)
    else:
        alignment_score = 0.5  # Neutral if no markers defined
    
    # 2. Check for drift indicators
    drift_markers = DRIFT_INDICATORS.get(intent_category, [])
    drift_count = 0
    
    for marker in drift_markers:
        if marker in response_lower:
            drift_count += 1
            drift_reasons.append(f"Drift indicator: '{marker}'")
    
    # Adjust score for drift
    if drift_count > 0:
        drift_penalty = min(0.3, drift_count * 0.1)
        alignment_score = max(0.0, alignment_score - drift_penalty)
    
    # 3. Check expected topics if provided
    if expected_topics:
        for topic in expected_topics:
            if topic.lower() in response_lower:
                matched_categories.append(topic)
            else:
                missed_categories.append(topic)
        
        # Adjust score based on topic coverage
        if expected_topics:
            topic_score = len(matched_categories) / len(expected_topics)
            alignment_score = (alignment_score + topic_score) / 2
    
    # 4. Check for semantic drift from intent keywords
    intent_keywords = set(re.findall(r'\b\w+\b', intent.lower()))
    response_keywords = set(re.findall(r'\b\w+\b', response_lower))
    
    # Filter out common words
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                 'can', 'need', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
                 'by', 'from', 'as', 'into', 'through', 'during', 'before',
                 'after', 'above', 'below', 'between', 'under', 'again',
                 'further', 'then', 'once', 'here', 'there', 'when', 'where',
                 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other',
                 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
                 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if',
                 'or', 'because', 'until', 'while', 'i', 'you', 'your', 'my'}
    
    intent_keywords -= stopwords
    response_keywords -= stopwords
    
    if intent_keywords:
        keyword_overlap = len(intent_keywords & response_keywords) / len(intent_keywords)
        # Keyword overlap is a secondary signal
        alignment_score = alignment_score * 0.7 + keyword_overlap * 0.3
    
    # 5. Determine drift
    drift_detected = len(drift_reasons) > 0 or alignment_score < 0.5
    
    # 6. Add structural drift checks
    if intent_category == IntentCategory.TASK_COMPLETION.value:
        # Check if task was actually completed
        if 'error' in response_lower or 'failed' in response_lower:
            drift_detected = True
            drift_reasons.append("Task completion response contains error/failure indicators")
    
    if intent_category == IntentCategory.INFORMATION_SEEKING.value:
        # Check if information was actually provided
        if len(response) < 50:  # Very short response
            drift_detected = True
            drift_reasons.append("Information seeking got very short response")
    
    # Clamp score
    alignment_score = max(0.0, min(1.0, alignment_score))
    
    return IntentAlignmentResult(
        aligned=alignment_score >= 0.5 and not drift_detected,
        score=alignment_score,
        drift_detected=drift_detected,
        drift_reasons=drift_reasons,
        matched_categories=matched_categories,
        missed_categories=missed_categories
    )


def validate_intent_alignment(
    contract: SelfReportContract,
    response: str,
    expected_topics: Optional[List[str]] = None
) -> IntentAlignmentResult:
    """
    Validate that a response aligns with the contract's stated intent.
    
    Args:
        contract: The self-report contract with intent
        response: The agent's response to validate
        expected_topics: Optional list of expected topics
    
    Returns:
        IntentAlignmentResult
    """
    return calculate_intent_alignment(
        intent=contract.intent,
        intent_category=contract.intent_category,
        response=response,
        expected_topics=expected_topics
    )


# ============================================
# Contract Generation for Shadow Mode
# ============================================

def generate_contract(
    user_text: str,
    target_id: Optional[str] = None,
    session_id: Optional[str] = None,
    source: str = "system",
    custom_intent: Optional[str] = None,
    custom_category: Optional[str] = None
) -> SelfReportContract:
    """
    Generate a self-report contract with intent alignment metadata.
    
    This function is intended for shadow mode operation where contracts
    are generated dynamically based on user input.
    
    Args:
        user_text: The user's input text
        target_id: Optional target identifier
        session_id: Optional session identifier
        source: Who is generating the contract
        custom_intent: Override the extracted intent
        custom_category: Override the classified category
    
    Returns:
        SelfReportContract with intent alignment fields populated
    """
    # Generate contract ID
    contract_id = hashlib.sha256(
        f"{user_text}{datetime.now(timezone.utc).isoformat()}".encode()
    ).hexdigest()[:16]
    
    # Classify intent
    if custom_intent:
        intent = custom_intent
    else:
        # Extract intent from user text (first 200 chars as summary)
        intent = user_text[:200] if len(user_text) > 200 else user_text
    
    if custom_category:
        intent_category = custom_category
    else:
        intent_category, _ = classify_intent(user_text)
    
    return SelfReportContract(
        contract_id=contract_id,
        intent=intent,
        intent_category=intent_category,
        intent_alignment_score=1.0,  # Will be updated after response
        intent_drift=False,
        intent_drift_reasons=[],
        contract_version="2.1",
        source=source,
        target_id=target_id,
        session_id=session_id
    )


def update_contract_with_alignment(
    contract: SelfReportContract,
    response: str,
    expected_topics: Optional[List[str]] = None
) -> SelfReportContract:
    """
    Update contract with alignment results after response is generated.
    
    Args:
        contract: The original contract
        response: The generated response
        expected_topics: Optional expected topics
    
    Returns:
        Updated SelfReportContract with alignment metadata
    """
    result = validate_intent_alignment(contract, response, expected_topics)
    
    contract.intent_alignment_score = result.score
    contract.intent_drift = result.drift_detected
    contract.intent_drift_reasons = result.drift_reasons
    
    return contract


# ============================================
# Shadow Mode Contract Logger
# ============================================

class ShadowModeContractLogger:
    """
    Logger for shadow mode contract validation.
    
    Records contracts and alignment results for offline analysis.
    """
    
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path or "/tmp/shadow_contracts.jsonl"
        self._contracts: List[Dict[str, Any]] = []
    
    def log_contract(self, contract: SelfReportContract) -> None:
        """Log a contract to the shadow log"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contract": contract.to_dict()
        }
        self._contracts.append(entry)
        
        # Write to file
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def log_alignment_result(
        self,
        contract: SelfReportContract,
        response: str,
        result: IntentAlignmentResult
    ) -> None:
        """Log alignment result"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contract_id": contract.contract_id,
            "intent": contract.intent,
            "intent_category": contract.intent_category,
            "alignment_score": result.score,
            "drift_detected": result.drift_detected,
            "drift_reasons": result.drift_reasons,
            "matched_categories": result.matched_categories,
            "missed_categories": result.missed_categories,
            "response_length": len(response)
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from logged contracts"""
        if not self._contracts:
            return {"total": 0}
        
        total = len(self._contracts)
        drift_count = sum(1 for c in self._contracts 
                        if c.get("contract", {}).get("intent_drift", False))
        avg_alignment = sum(c.get("contract", {}).get("intent_alignment_score", 1.0) 
                          for c in self._contracts) / total
        
        return {
            "total": total,
            "drift_count": drift_count,
            "drift_rate": drift_count / total if total > 0 else 0,
            "average_alignment_score": avg_alignment
        }


# ============================================
# CLI Entry Point
# ============================================

def main():
    """CLI interface for self-report contract operations"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Self-Report Contract v2.1')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate a contract')
    gen_parser.add_argument('text', help='User text to generate contract from')
    gen_parser.add_argument('--target-id', help='Target identifier')
    gen_parser.add_argument('--session-id', help='Session identifier')
    gen_parser.add_argument('--intent', help='Custom intent override')
    gen_parser.add_argument('--category', help='Custom category override')
    
    # Validate command
    val_parser = subparsers.add_parser('validate', help='Validate alignment')
    val_parser.add_argument('--contract', required=True, help='Contract JSON file')
    val_parser.add_argument('--response', required=True, help='Response text file or string')
    val_parser.add_argument('--topics', nargs='+', help='Expected topics')
    
    # Classify command
    cls_parser = subparsers.add_parser('classify', help='Classify intent')
    cls_parser.add_argument('text', help='Text to classify')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        contract = generate_contract(
            user_text=args.text,
            target_id=args.target_id,
            session_id=args.session_id,
            custom_intent=args.intent,
            custom_category=args.category
        )
        print(contract.to_json())
    
    elif args.command == 'validate':
        with open(args.contract) as f:
            contract = SelfReportContract.from_json(f.read())
        
        # Try to read as file, otherwise use as string
        try:
            with open(args.response) as f:
                response = f.read()
        except FileNotFoundError:
            response = args.response
        
        result = validate_intent_alignment(contract, response, args.topics)
        
        output = {
            "aligned": result.aligned,
            "score": result.score,
            "drift_detected": result.drift_detected,
            "drift_reasons": result.drift_reasons,
            "matched_categories": result.matched_categories,
            "missed_categories": result.missed_categories
        }
        print(json.dumps(output, indent=2))
    
    elif args.command == 'classify':
        category, confidence = classify_intent(args.text)
        print(f"Category: {category}")
        print(f"Confidence: {confidence:.3f}")
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
