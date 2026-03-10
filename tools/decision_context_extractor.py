#!/usr/bin/env python3
"""
decision_context_extractor.py - Enhanced Decision Context Extraction

Purpose:
  Extract decision_context from text with higher coverage and precision.
  This is a focused enhancement to address the 0% coverage issue.

Usage:
  decision_context_extractor.py --input <text>
  decision_context_extractor.py --test
  decision_context_extractor.py --jsonl <file>
"""

import argparse
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Decision:
    """Represents an extracted decision."""
    what: str           # The decision made
    why: Optional[str]  # The rationale
    pattern_type: str   # Which pattern matched
    confidence: float   # Extraction confidence (0-1)


def extract_decision_context(content: str) -> Dict:
    """
    Extract decision_context from text.
    
    Returns a structured decision_context object.
    """
    if not content or len(content.strip()) < 10:
        return {
            "present": False,
            "decisions": [],
            "extraction_confidence": 0.0
        }
    
    decisions = []
    
    # === Pattern 1: Explicit Decision with Rationale ===
    # "决定X因为Y", "选择X由于Y"
    pattern1 = r'(决定|选择|采用|确认|切换到)[^\n]{5,50}?[因为由于]([^\n]{5,100})'
    for match in re.finditer(pattern1, content):
        decision_text = match.group(0)
        rationale = match.group(2) if len(match.groups()) >= 2 else None
        
        # Extract the decision part (before 因为/由于)
        decision_part = re.sub(r'[因为由于].*$', '', decision_text)
        
        decisions.append(Decision(
            what=decision_part.strip(),
            why=rationale.strip() if rationale else None,
            pattern_type="explicit_with_rationale",
            confidence=0.9
        ))
    
    # === Pattern 2: Rationale-Decision Link ===
    # "因为Y，所以决定X"
    pattern2 = r'[因为由于]([^\n]{5,50}?)[，,]?\s*所以[选择决定采用]?([^\n]{5,50})'
    for match in re.finditer(pattern2, content):
        decisions.append(Decision(
            what=match.group(2).strip(),
            why=match.group(1).strip(),
            pattern_type="rationale_first",
            confidence=0.85
        ))
    
    # === Pattern 3: Trade-off Resolution ===
    # "虽然X，但是Y，决定Z"
    pattern3 = r'虽然[^\n]{5,30}，但是[^\n]{5,30}[，,]?\s*(决定|选择|采用)[^\n]{5,50}'
    for match in re.finditer(pattern3, content):
        decision_text = match.group(0)
        # Extract the final decision
        decision_part = re.search(r'(决定|选择|采用)[^\n]+', decision_text)
        if decision_part:
            decisions.append(Decision(
                what=decision_part.group(0).strip(),
                why="权衡后的选择",
                pattern_type="trade_off",
                confidence=0.8
            ))
    
    # === Pattern 4: Simple Decision Marker ===
    # "决定X", "选择Y", "采用Z"
    # Lower confidence, but catches cases without explicit rationale
    pattern4 = r'(决定|选择|采用|确认|切换到)([^\n，,。]{5,40})'
    for match in re.finditer(pattern4, content):
        decision_text = match.group(2).strip()
        
        # Skip if already captured by higher-confidence patterns
        if any(d.what in match.group(0) for d in decisions):
            continue
        
        # Skip common false positives
        false_positive_indicators = ['下一步', '然后', '之后', '准备']
        if any(fp in match.group(0) for fp in false_positive_indicators):
            continue
        
        decisions.append(Decision(
            what=f"{match.group(1)}{decision_text}",
            why=None,
            pattern_type="simple_marker",
            confidence=0.6
        ))
    
    # === Pattern 5: Problem-Solution Link ===
    # "为了解决X，我们Y"
    pattern5 = r'为了[解决处理修复]([^\n]{5,40})[，,]?\s*我们([^\n]{5,50})'
    for match in re.finditer(pattern5, content):
        decisions.append(Decision(
            what=match.group(2).strip(),
            why=f"为了解决: {match.group(1).strip()}",
            pattern_type="problem_solution",
            confidence=0.75
        ))
    
    # === Pattern 6: Conclusion Marker ===
    # "结论是X", "最终方案是Y"
    pattern6 = r'(结论是|最终方案是|选定)[^\n]{5,60}'
    for match in re.finditer(pattern6, content):
        decisions.append(Decision(
            what=match.group(0).strip(),
            why="经过评估的结论",
            pattern_type="conclusion",
            confidence=0.7
        ))
    
    # Sort by confidence
    decisions.sort(key=lambda d: -d.confidence)
    
    # Take top decision
    top_decision = decisions[0] if decisions else None
    
    return {
        "present": top_decision is not None,
        "decisions": [
            {
                "what": d.what,
                "why": d.why,
                "pattern_type": d.pattern_type,
                "confidence": d.confidence
            }
            for d in decisions[:3]  # Top 3 decisions
        ],
        "last_decision": {
            "what": top_decision.what,
            "why": top_decision.why
        } if top_decision else None,
        "extraction_confidence": top_decision.confidence if top_decision else 0.0
    }


def extract_from_jsonl(path: str) -> List[Dict]:
    """Extract decision_context from a JSONL file of samples."""
    results = []
    
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                
                # Get content
                content = record.get("content", "")
                if not content:
                    # Try other fields
                    content = record.get("sample_id", "")
                    content += " " + record.get("human_reason", "")
                
                # Extract
                dc = extract_decision_context(content)
                
                results.append({
                    "sample_id": record.get("sample_id", "unknown"),
                    "decision_context": dc
                })
                
            except json.JSONDecodeError:
                continue
    
    return results


def run_tests():
    """Run extraction tests."""
    test_cases = [
        {
            "input": "经过对比，我们决定采用 gate-based scoring，因为阈值法在 stress test 中 FP 率太高。",
            "expected_present": True,
            "expected_keyword": "gate-based scoring"
        },
        {
            "input": "虽然 V2 实现复杂度更高，但它提供了更好的可解释性，权衡后决定继续使用 V2。",
            "expected_present": True,
            "expected_keyword": "V2"
        },
        {
            "input": "为了解决 long_technical 的 FP 问题，我们在 rubric 中增加了 decision_context 权重。",
            "expected_present": True,
            "expected_keyword": "decision_context"
        },
        {
            "input": "我们评估了方案A和方案B，最终选择方案B，因为改动范围更可控。",
            "expected_present": True,
            "expected_keyword": "方案B"
        },
        {
            "input": "当前任务是实现 Context Compression Pipeline。",
            "expected_present": False,
            "expected_keyword": None
        },
        {
            "input": "X是Y的一部分，我们需要继续执行。",
            "expected_present": False,
            "expected_keyword": None
        },
        {
            "input": "下一步运行 shadow validation。",
            "expected_present": False,
            "expected_keyword": None
        }
    ]
    
    print("=== Decision Context Extraction Tests ===\n")
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        result = extract_decision_context(test["input"])
        
        # Check if result matches expected
        actual_present = result["present"]
        expected_present = test["expected_present"]
        
        if actual_present == expected_present:
            # If present, also check keyword
            if expected_present and test["expected_keyword"]:
                if test["expected_keyword"] in str(result.get("last_decision", {})):
                    status = "✅ PASS"
                    passed += 1
                else:
                    status = "⚠️ PARTIAL (keyword not found)"
                    passed += 0.5
            else:
                status = "✅ PASS"
                passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"Test {i}: {status}")
        print(f"  Input: {test['input'][:60]}...")
        print(f"  Expected present: {expected_present}, Got: {actual_present}")
        if result["present"]:
            print(f"  Extracted: {result.get('last_decision')}")
        print()
    
    print(f"Results: {passed}/{len(test_cases)} passed")
    
    return failed == 0


def main():
    parser = argparse.ArgumentParser(description="Decision Context Extractor")
    parser.add_argument("--input", help="Input text to extract from")
    parser.add_argument("--jsonl", help="JSONL file to process")
    parser.add_argument("--test", action="store_true", help="Run tests")
    
    args = parser.parse_args()
    
    if args.test:
        success = run_tests()
        return 0 if success else 1
    
    if args.input:
        result = extract_decision_context(args.input)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    
    if args.jsonl:
        results = extract_from_jsonl(args.jsonl)
        
        # Calculate coverage
        total = len(results)
        present = sum(1 for r in results if r["decision_context"]["present"])
        
        print(f"Processed: {total} samples")
        print(f"Decision context present: {present} ({present/total*100:.1f}%)")
        
        # Save results
        output_path = args.jsonl.replace(".jsonl", "_decision_context.json")
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to: {output_path}")
        return 0
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    exit(main())
