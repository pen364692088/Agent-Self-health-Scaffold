#!/usr/bin/env python3
"""
Anchor-Aware Ranking A/B Test for Old-Topic Micro-Benchmark

Tests:
  A = Baseline retrieve (keyword-based ranking)
  B = Anchor-aware ranking (based on 6 anchor types)

Anchor Priority:
  1. decision_anchor
  2. entity_anchor
  3. time_anchor
  4. open_loop_anchor
  5. constraint_anchor
  6. tool_state_anchor
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
SAMPLES_DIR = WORKSPACE / "artifacts" / "context_compression" / "validation" / "samples"
BENCHMARK_DEF = WORKSPACE / "artifacts" / "context_compression" / "anchor-binding" / "old_topic_micro_benchmark_12.json"
OUTPUT_DIR = WORKSPACE / "artifacts" / "context_compression" / "anchor-binding"

# Anchor priorities (higher = more important)
ANCHOR_PRIORITIES = {
    "decision_anchor": 6,
    "entity_anchor": 5,
    "time_anchor": 4,
    "open_loop_anchor": 3,
    "constraint_anchor": 2,
    "tool_state_anchor": 1,
}


@dataclass
class Anchor:
    """Represents a single anchor extracted from events."""
    anchor_type: str
    content: str
    timestamp: str
    priority: int = 0
    
    def __post_init__(self):
        self.priority = ANCHOR_PRIORITIES.get(self.anchor_type, 0)


@dataclass
class Capsule:
    """Simulated capsule for testing."""
    capsule_id: str
    session_id: str
    topic: str
    summary: str
    decisions: List[Dict] = field(default_factory=list)
    entities: List[Dict] = field(default_factory=list)
    time_refs: List[str] = field(default_factory=list)
    open_loops: List[Dict] = field(default_factory=list)
    hard_constraints: List[str] = field(default_factory=list)
    tool_states: List[Dict] = field(default_factory=list)
    retrieval_keys: List[str] = field(default_factory=list)
    
    def get_anchors(self) -> List[Anchor]:
        """Extract anchors from capsule."""
        anchors = []
        
        for d in self.decisions:
            anchors.append(Anchor(
                anchor_type="decision_anchor",
                content=str(d),
                timestamp="",
                priority=ANCHOR_PRIORITIES["decision_anchor"]
            ))
        
        for e in self.entities:
            anchors.append(Anchor(
                anchor_type="entity_anchor",
                content=e.get("name", ""),
                timestamp="",
                priority=ANCHOR_PRIORITIES["entity_anchor"]
            ))
        
        for t in self.time_refs:
            anchors.append(Anchor(
                anchor_type="time_anchor",
                content=t,
                timestamp="",
                priority=ANCHOR_PRIORITIES["time_anchor"]
            ))
        
        for ol in self.open_loops:
            anchors.append(Anchor(
                anchor_type="open_loop_anchor",
                content=str(ol),
                timestamp="",
                priority=ANCHOR_PRIORITIES["open_loop_anchor"]
            ))
        
        for c in self.hard_constraints:
            anchors.append(Anchor(
                anchor_type="constraint_anchor",
                content=c,
                timestamp="",
                priority=ANCHOR_PRIORITIES["constraint_anchor"]
            ))
        
        for ts in self.tool_states:
            anchors.append(Anchor(
                anchor_type="tool_state_anchor",
                content=str(ts),
                timestamp="",
                priority=ANCHOR_PRIORITIES["tool_state_anchor"]
            ))
        
        return anchors


class AnchorExtractor:
    """Extract anchors from events."""
    
    DECISION_PATTERNS = [
        r"(?:decided|decision|we will|let's|chose|selected|采用|决定|选择)",
        r"(?:use|using|implement|采用方案|使用方案)",
    ]
    
    ENTITY_PATTERNS = [
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",  # Proper nouns
        r"([a-z_]+\.py|[a-z_]+\.js|[a-z_]+\.ts)",  # File names
        r"([A-Z_]+)",  # Constants/IDs
    ]
    
    TIME_PATTERNS = [
        r"\d{4}-\d{2}-\d{2}",
        r"\d{1,2}:\d{2}",
        r"(?:today|tomorrow|yesterday|next|last)",
        r"(?:今天|明天|昨天|下周|上周)",
    ]
    
    CONSTRAINT_PATTERNS = [
        r"(?:must|should|need to|cannot|don't|avoid|required|必须|需要|禁止)",
        r"(?:constraint|limitation|restriction|限制|约束)",
    ]
    
    OPEN_LOOP_PATTERNS = [
        r"(?:TODO|FIXME|pending|waiting|later|待|待办|后续)",
        r"(?:not yet|incomplete|unfinished|未完成)",
    ]
    
    TOOL_STATE_PATTERNS = [
        r"(?:running|executing|completed|failed|success)",
        r"(?:tool|command|script|process)",
    ]
    
    def extract_from_events(self, events: List[Dict]) -> Capsule:
        """Extract anchors from a list of events."""
        decisions = []
        entities = defaultdict(int)
        time_refs = []
        open_loops = []
        constraints = []
        tool_states = []
        
        all_text = []
        for event in events:
            content = event.get("content", "")
            if content:
                all_text.append(content)
            
            # Extract tool states
            tool_name = event.get("tool_name", "")
            if tool_name:
                tool_states.append({
                    "tool": tool_name,
                    "event_type": event.get("event_type", ""),
                    "timestamp": event.get("timestamp", "")
                })
        
        combined_text = "\n".join(all_text)
        
        # Extract decisions
        for pattern in self.DECISION_PATTERNS:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for m in matches[:5]:  # Limit to 5
                if isinstance(m, tuple):
                    m = m[0] if m else ""
                if m and len(m) > 5:
                    decisions.append({"decision": m[:200]})
        
        # Extract entities
        for pattern in self.ENTITY_PATTERNS:
            matches = re.findall(pattern, combined_text)
            for m in matches:
                if isinstance(m, tuple):
                    m = m[0] if m else ""
                if m and len(m) > 2:
                    entities[m] += 1
        
        # Extract time references
        for pattern in self.TIME_PATTERNS:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            time_refs.extend(matches[:3])
        
        # Extract constraints
        for pattern in self.CONSTRAINT_PATTERNS:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for m in matches[:3]:
                if isinstance(m, tuple):
                    m = m[0] if m else ""
                if m:
                    constraints.append(m[:100])
        
        # Extract open loops
        for pattern in self.OPEN_LOOP_PATTERNS:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for m in matches[:3]:
                if isinstance(m, tuple):
                    m = m[0] if m else ""
                if m:
                    open_loops.append({"item": m[:100]})
        
        # Build entity list
        entity_list = [
            {"name": name, "type": "extracted", "mentions": count}
            for name, count in sorted(entities.items(), key=lambda x: -x[1])[:10]
        ]
        
        # Generate topic/summary from first meaningful content
        topic = "Unknown topic"
        summary = ""
        for text in all_text[:5]:
            if len(text) > 20:
                # Try to extract title/heading
                lines = text.split("\n")
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("```") and len(line) < 100:
                        topic = line[:80]
                        break
                break
        
        return Capsule(
            capsule_id=f"cap_{events[0].get('session_id', 'unknown')[:8] if events else 'unknown'}",
            session_id=events[0].get("session_id", "") if events else "",
            topic=topic,
            summary=summary or f"Extracted from {len(events)} events",
            decisions=decisions[:5],
            entities=entity_list,
            time_refs=list(set(time_refs))[:5],
            open_loops=open_loops[:3],
            hard_constraints=list(set(constraints))[:5],
            tool_states=tool_states[:10],
            retrieval_keys=list(entities.keys())[:10]
        )


class BaselineRetriever:
    """Baseline keyword-based retrieval (A)."""
    
    def _keyword_match(self, query: str, text: str) -> float:
        """Calculate keyword match score."""
        if not query or not text:
            return 0.0
        
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Extract keywords (Chinese + English 3+ chars)
        query_keywords = set(re.findall(r'\b[\u4e00-\u9fff]+\b|[a-zA-Z]{3,}\b', query_lower))
        
        if not query_keywords:
            return 0.0
        
        matches = sum(1 for kw in query_keywords if kw in text_lower)
        return matches / len(query_keywords)
    
    def retrieve(self, capsules: List[Capsule], query: str, top_k: int = 5) -> List[Tuple[Capsule, float]]:
        """Retrieve capsules using keyword matching."""
        results = []
        
        for capsule in capsules:
            # Build searchable text
            search_fields = [
                capsule.topic,
                capsule.summary,
                ' '.join(capsule.retrieval_keys),
                ' '.join([str(d) for d in capsule.decisions]),
                ' '.join(capsule.hard_constraints),
                ' '.join([e.get("name", "") for e in capsule.entities])
            ]
            search_text = ' '.join(search_fields)
            
            score = self._keyword_match(query, search_text)
            
            if score > 0:
                results.append((capsule, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


class AnchorAwareRetriever:
    """Anchor-aware retrieval (B)."""
    
    def __init__(self, anchor_priorities: Dict[str, int] = None):
        self.anchor_priorities = anchor_priorities or ANCHOR_PRIORITIES
    
    def _keyword_match(self, query: str, text: str) -> float:
        """Calculate keyword match score."""
        if not query or not text:
            return 0.0
        
        query_lower = query.lower()
        text_lower = text.lower()
        
        query_keywords = set(re.findall(r'\b[\u4e00-\u9fff]+\b|[a-zA-Z]{3,}\b', query_lower))
        
        if not query_keywords:
            return 0.0
        
        matches = sum(1 for kw in query_keywords if kw in text_lower)
        return matches / len(query_keywords)
    
    def _anchor_overlap_score(self, query_anchors: List[Anchor], capsule_anchors: List[Anchor]) -> float:
        """Calculate anchor overlap score with priority weighting."""
        if not query_anchors or not capsule_anchors:
            return 0.0
        
        # Group anchors by type
        query_by_type = defaultdict(set)
        for a in query_anchors:
            query_by_type[a.anchor_type].add(a.content.lower())
        
        capsule_by_type = defaultdict(set)
        for a in capsule_anchors:
            capsule_by_type[a.anchor_type].add(a.content.lower())
        
        # Calculate weighted overlap
        total_weight = 0.0
        total_possible = 0.0
        
        for anchor_type, priority in self.anchor_priorities.items():
            query_set = query_by_type.get(anchor_type, set())
            capsule_set = capsule_by_type.get(anchor_type, set())
            
            if query_set:
                # This anchor type is relevant to the query
                weight = priority
                total_possible += weight
                
                if capsule_set:
                    # Calculate overlap
                    overlap = len(query_set & capsule_set)
                    coverage = overlap / len(query_set) if query_set else 0
                    total_weight += weight * coverage
        
        return total_weight / total_possible if total_possible > 0 else 0.0
    
    def retrieve(self, capsules: List[Capsule], query: str, query_anchors: List[Anchor], top_k: int = 5) -> List[Tuple[Capsule, float, Dict]]:
        """Retrieve capsules using anchor-aware ranking."""
        results = []
        
        for capsule in capsules:
            # 1. Base keyword score
            search_fields = [
                capsule.topic,
                capsule.summary,
                ' '.join(capsule.retrieval_keys),
            ]
            search_text = ' '.join(search_fields)
            keyword_score = self._keyword_match(query, search_text)
            
            # 2. Anchor overlap score
            capsule_anchors = capsule.get_anchors()
            anchor_score = self._anchor_overlap_score(query_anchors, capsule_anchors)
            
            # 3. Combined score (70% keyword + 30% anchor)
            # This ensures we don't deviate too much from baseline
            combined_score = 0.7 * keyword_score + 0.3 * anchor_score
            
            if combined_score > 0:
                # Calculate anchor match details
                anchor_matches = {}
                query_by_type = defaultdict(set)
                for a in query_anchors:
                    query_by_type[a.anchor_type].add(a.content.lower())
                
                capsule_by_type = defaultdict(set)
                for a in capsule_anchors:
                    capsule_by_type[a.anchor_type].add(a.content.lower())
                
                for anchor_type in self.anchor_priorities.keys():
                    query_set = query_by_type.get(anchor_type, set())
                    capsule_set = capsule_by_type.get(anchor_type, set())
                    
                    if query_set and capsule_set:
                        overlap = query_set & capsule_set
                        if overlap:
                            anchor_matches[anchor_type] = {
                                "query_count": len(query_set),
                                "capsule_count": len(capsule_set),
                                "overlap": list(overlap)[:5]
                            }
                
                results.append((capsule, combined_score, {
                    "keyword_score": round(keyword_score, 3),
                    "anchor_score": round(anchor_score, 3),
                    "combined_score": round(combined_score, 3),
                    "anchor_matches": anchor_matches
                }))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


class ABTestRunner:
    """Run A/B test on micro-benchmark."""
    
    def __init__(self):
        self.extractor = AnchorExtractor()
        self.baseline_retriever = BaselineRetriever()
        self.anchor_retriever = AnchorAwareRetriever()
    
    def load_sample(self, sample_path: Path) -> Dict:
        """Load a sample file."""
        with open(sample_path, 'r') as f:
            return json.load(f)
    
    def generate_query(self, sample: Dict) -> str:
        """Generate a test query from sample."""
        # For old-topic recall, simulate a user asking about previous work
        topic_hints = []
        
        # Extract topic hints from events
        events = sample.get("events", [])
        for event in events[:20]:
            content = event.get("content", "")
            if content and len(content) > 50:
                # Look for task/topic indicators
                if "Task" in content or "task" in content:
                    lines = content.split("\n")
                    for line in lines[:3]:
                        if "Task" in line or "task" in line:
                            topic_hints.append(line.strip()[:100])
                            break
        
        if topic_hints:
            return f"what was the {topic_hints[0][:50]}"
        
        return "what was discussed previously about the task"
    
    def extract_query_anchors(self, sample: Dict) -> List[Anchor]:
        """Extract anchors that should be matched for this query."""
        # For old-topic recall, extract anchors from recent events
        events = sample.get("events", [])
        
        # Use last 10 events to extract what the user might be asking about
        recent_events = events[-10:] if len(events) > 10 else events
        capsule = self.extractor.extract_from_events(recent_events)
        
        return capsule.get_anchors()
    
    def build_test_capsules(self, sample: Dict) -> List[Capsule]:
        """Build test capsules from sample events."""
        events = sample.get("events", [])
        
        # Split events into segments to create multiple capsules
        capsules = []
        segment_size = 20
        
        for i in range(0, len(events), segment_size):
            segment = events[i:i+segment_size]
            if segment:
                capsule = self.extractor.extract_from_events(segment)
                capsule.capsule_id = f"{sample.get('sample_id', 'unknown')}_seg{i//segment_size}"
                capsules.append(capsule)
        
        # Also create a "previous session" capsule from early events
        if len(events) > segment_size:
            early_events = events[:segment_size]
            early_capsule = self.extractor.extract_from_events(early_events)
            early_capsule.capsule_id = f"{sample.get('sample_id', 'unknown')}_early"
            capsules.append(early_capsule)
        
        return capsules
    
    def evaluate_result(self, capsule: Capsule, query_anchors: List[Anchor]) -> Dict:
        """Evaluate if a retrieved capsule matches the expected anchors."""
        capsule_anchors = capsule.get_anchors()
        
        # Check anchor overlap
        query_by_type = defaultdict(set)
        for a in query_anchors:
            query_by_type[a.anchor_type].add(a.content.lower())
        
        capsule_by_type = defaultdict(set)
        for a in capsule_anchors:
            capsule_by_type[a.anchor_type].add(a.content.lower())
        
        anchor_overlaps = {}
        for anchor_type in ANCHOR_PRIORITIES.keys():
            query_set = query_by_type.get(anchor_type, set())
            capsule_set = capsule_by_type.get(anchor_type, set())
            
            if query_set:
                overlap = query_set & capsule_set
                anchor_overlaps[anchor_type] = {
                    "expected": len(query_set),
                    "found": len(capsule_set),
                    "overlap": len(overlap),
                    "coverage": len(overlap) / len(query_set) if query_set else 0
                }
        
        # Calculate metrics
        total_expected = sum(v["expected"] for v in anchor_overlaps.values())
        total_overlap = sum(v["overlap"] for v in anchor_overlaps.values())
        coverage = total_overlap / total_expected if total_expected > 0 else 0
        
        # Top-1 anchor hit: did we hit at least one high-priority anchor?
        top1_hit = False
        for anchor_type in ["decision_anchor", "entity_anchor", "time_anchor"]:
            if anchor_type in anchor_overlaps and anchor_overlaps[anchor_type]["overlap"] > 0:
                top1_hit = True
                break
        
        return {
            "anchor_overlaps": anchor_overlaps,
            "coverage": round(coverage, 3),
            "top1_anchor_hit": top1_hit,
            "total_expected": total_expected,
            "total_overlap": total_overlap
        }
    
    def run_single_sample(self, sample_path: Path) -> Dict:
        """Run A/B test on a single sample."""
        sample = self.load_sample(sample_path)
        sample_id = sample.get("sample_id", sample_path.stem)
        
        # Generate query and anchors
        query = self.generate_query(sample)
        query_anchors = self.extract_query_anchors(sample)
        
        # Build test capsules
        capsules = self.build_test_capsules(sample)
        
        # A: Baseline retrieval
        baseline_results = self.baseline_retriever.retrieve(capsules, query, top_k=3)
        
        # B: Anchor-aware retrieval
        anchor_results = self.anchor_retriever.retrieve(capsules, query, query_anchors, top_k=3)
        
        # Evaluate results
        baseline_eval = {}
        anchor_eval = {}
        
        if baseline_results:
            top_capsule, score = baseline_results[0]
            baseline_eval = self.evaluate_result(top_capsule, query_anchors)
            baseline_eval["score"] = round(score, 3)
        
        if anchor_results:
            top_capsule, score, details = anchor_results[0]
            anchor_eval = self.evaluate_result(top_capsule, query_anchors)
            anchor_eval["score"] = round(score, 3)
            anchor_eval["details"] = details
        
        return {
            "sample_id": sample_id,
            "source_type": sample.get("source_type", ""),
            "bucket_tags": sample.get("bucket_tags", []),
            "query": query,
            "capsules_count": len(capsules),
            "query_anchors_count": len(query_anchors),
            "baseline": {
                "top1_result": baseline_results[0][0].capsule_id if baseline_results else None,
                **baseline_eval
            },
            "anchor_aware": {
                "top1_result": anchor_results[0][0].capsule_id if anchor_results else None,
                **anchor_eval
            },
            "comparison": {
                "coverage_delta": (anchor_eval.get("coverage", 0) - baseline_eval.get("coverage", 0)),
                "top1_hit_improved": anchor_eval.get("top1_anchor_hit", False) and not baseline_eval.get("top1_anchor_hit", False),
                "score_delta": (anchor_eval.get("score", 0) - baseline_eval.get("score", 0))
            }
        }
    
    def run_benchmark(self, benchmark_def: Path) -> Dict:
        """Run A/B test on entire benchmark."""
        with open(benchmark_def, 'r') as f:
            benchmark = json.load(f)
        
        results = []
        sample_ids = [item["sample_id"] for item in benchmark["items"]]
        
        for sample_id in sample_ids:
            sample_path = SAMPLES_DIR / f"{sample_id}.json"
            if sample_path.exists():
                result = self.run_single_sample(sample_path)
                results.append(result)
            else:
                print(f"Warning: Sample not found: {sample_path}")
        
        # Calculate aggregate metrics
        total_samples = len(results)
        
        # Baseline metrics
        baseline_coverages = [r["baseline"].get("coverage", 0) for r in results]
        baseline_top1_hits = sum(1 for r in results if r["baseline"].get("top1_anchor_hit", False))
        
        # Anchor-aware metrics
        anchor_coverages = [r["anchor_aware"].get("coverage", 0) for r in results]
        anchor_top1_hits = sum(1 for r in results if r["anchor_aware"].get("top1_anchor_hit", False))
        
        # Comparison
        coverage_deltas = [r["comparison"]["coverage_delta"] for r in results]
        improved_count = sum(1 for r in results if r["comparison"]["coverage_delta"] > 0)
        degraded_count = sum(1 for r in results if r["comparison"]["coverage_delta"] < 0)
        
        # Correct topic, wrong anchor detection
        correct_topic_wrong_anchor_baseline = sum(
            1 for r in results 
            if r["baseline"].get("coverage", 0) > 0 and r["baseline"].get("coverage", 0) < 0.5
        )
        correct_topic_wrong_anchor_anchor = sum(
            1 for r in results 
            if r["anchor_aware"].get("coverage", 0) > 0 and r["anchor_aware"].get("coverage", 0) < 0.5
        )
        
        # >=0.75 samples
        baseline_075_plus = sum(1 for c in baseline_coverages if c >= 0.75)
        anchor_075_plus = sum(1 for c in anchor_coverages if c >= 0.75)
        
        aggregate = {
            "total_samples": total_samples,
            "baseline": {
                "avg_coverage": round(sum(baseline_coverages) / total_samples, 3) if total_samples > 0 else 0,
                "top1_anchor_hit_rate": round(baseline_top1_hits / total_samples, 3) if total_samples > 0 else 0,
                "samples_075_plus": baseline_075_plus,
                "correct_topic_wrong_anchor": correct_topic_wrong_anchor_baseline
            },
            "anchor_aware": {
                "avg_coverage": round(sum(anchor_coverages) / total_samples, 3) if total_samples > 0 else 0,
                "top1_anchor_hit_rate": round(anchor_top1_hits / total_samples, 3) if total_samples > 0 else 0,
                "samples_075_plus": anchor_075_plus,
                "correct_topic_wrong_anchor": correct_topic_wrong_anchor_anchor
            },
            "delta": {
                "avg_coverage": round((sum(anchor_coverages) - sum(baseline_coverages)) / total_samples, 3) if total_samples > 0 else 0,
                "top1_anchor_hit_rate": round((anchor_top1_hits - baseline_top1_hits) / total_samples, 3) if total_samples > 0 else 0,
                "samples_075_plus": anchor_075_plus - baseline_075_plus,
                "improved_count": improved_count,
                "degraded_count": degraded_count
            }
        }
        
        return {
            "benchmark_name": benchmark.get("name", "unknown"),
            "run_at": datetime.now().isoformat(),
            "aggregate": aggregate,
            "per_sample_results": results
        }


def generate_report(results: Dict) -> str:
    """Generate markdown report from results."""
    agg = results["aggregate"]
    
    report = f"""# A/B Benchmark Report: Anchor-Aware Ranking

**Benchmark**: {results["benchmark_name"]}
**Run At**: {results["run_at"]}

## Summary

| Metric | Baseline (A) | Anchor-Aware (B) | Delta |
|--------|-------------|------------------|-------|
| Avg Coverage | {agg["baseline"]["avg_coverage"]:.3f} | {agg["anchor_aware"]["avg_coverage"]:.3f} | {agg["delta"]["avg_coverage"]:+.3f} |
| Top-1 Anchor Hit Rate | {agg["baseline"]["top1_anchor_hit_rate"]:.1%} | {agg["anchor_aware"]["top1_anchor_hit_rate"]:.1%} | {agg["delta"]["top1_anchor_hit_rate"]:+.1%} |
| Samples >= 0.75 | {agg["baseline"]["samples_075_plus"]} | {agg["anchor_aware"]["samples_075_plus"]} | {agg["delta"]["samples_075_plus"]:+d} |
| Correct Topic, Wrong Anchor | {agg["baseline"]["correct_topic_wrong_anchor"]} | {agg["anchor_aware"]["correct_topic_wrong_anchor"]} | {agg["anchor_aware"]["correct_topic_wrong_anchor"] - agg["baseline"]["correct_topic_wrong_anchor"]:+d} |

## Key Findings

- **Total Samples**: {agg["total_samples"]}
- **Improved**: {agg["delta"]["improved_count"]} samples
- **Degraded**: {agg["delta"]["degraded_count"]} samples

## Per-Sample Results

| Sample ID | Source | Baseline Coverage | Anchor Coverage | Delta | Top1 Hit (B) |
|-----------|--------|------------------|-----------------|-------|--------------|
"""
    
    for r in results["per_sample_results"]:
        baseline_cov = r["baseline"].get("coverage", 0)
        anchor_cov = r["anchor_aware"].get("coverage", 0)
        delta = r["comparison"]["coverage_delta"]
        top1_hit = "✓" if r["anchor_aware"].get("top1_anchor_hit", False) else ""
        
        report += f"| {r['sample_id'][:40]} | {r['source_type'][:15]} | {baseline_cov:.3f} | {anchor_cov:.3f} | {delta:+.3f} | {top1_hit} |\n"
    
    report += f"""
## Recommendation

"""
    
    # Determine recommendation
    avg_delta = agg["delta"]["avg_coverage"]
    hit_rate_delta = agg["delta"]["top1_anchor_hit_rate"]
    
    if avg_delta > 0.05 or hit_rate_delta > 0.1:
        report += """**✅ RECOMMEND**: Anchor-aware ranking shows significant improvement and is worth pursuing.

Next steps:
1. Integrate anchor extraction into capsule builder
2. Add anchor scoring to retrieve pipeline
3. Run full S1 validation with new ranking
"""
    elif avg_delta > 0 or hit_rate_delta > 0:
        report += """**⚠️ MARGINAL**: Anchor-aware ranking shows small improvement. Consider further tuning before integration.

Suggested experiments:
1. Adjust anchor weight in combined score
2. Refine anchor extraction patterns
3. Test with larger benchmark
"""
    else:
        report += """**❌ NOT RECOMMENDED**: Anchor-aware ranking does not show improvement over baseline.

Possible reasons:
1. Anchor extraction quality insufficient
2. Weight combination not optimal
3. Benchmark samples not representative
"""
    
    return report


def main():
    print("Running A/B Benchmark: Anchor-Aware Ranking vs Baseline")
    print("=" * 60)
    
    runner = ABTestRunner()
    results = runner.run_benchmark(BENCHMARK_DEF)
    
    # Save JSON results
    output_json = OUTPUT_DIR / "ab_benchmark_results.json"
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_json}")
    
    # Generate and save report
    report = generate_report(results)
    output_md = OUTPUT_DIR / "ab_benchmark_report.md"
    with open(output_md, 'w') as f:
        f.write(report)
    print(f"Report saved to: {output_md}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    agg = results["aggregate"]
    print(f"Total Samples: {agg['total_samples']}")
    print(f"\nBaseline (A):")
    print(f"  - Avg Coverage: {agg['baseline']['avg_coverage']:.3f}")
    print(f"  - Top-1 Hit Rate: {agg['baseline']['top1_anchor_hit_rate']:.1%}")
    print(f"  - Samples >= 0.75: {agg['baseline']['samples_075_plus']}")
    print(f"\nAnchor-Aware (B):")
    print(f"  - Avg Coverage: {agg['anchor_aware']['avg_coverage']:.3f}")
    print(f"  - Top-1 Hit Rate: {agg['anchor_aware']['top1_anchor_hit_rate']:.1%}")
    print(f"  - Samples >= 0.75: {agg['anchor_aware']['samples_075_plus']}")
    print(f"\nDelta:")
    print(f"  - Avg Coverage: {agg['delta']['avg_coverage']:+.3f}")
    print(f"  - Improved: {agg['delta']['improved_count']}, Degraded: {agg['delta']['degraded_count']}")


if __name__ == "__main__":
    main()
