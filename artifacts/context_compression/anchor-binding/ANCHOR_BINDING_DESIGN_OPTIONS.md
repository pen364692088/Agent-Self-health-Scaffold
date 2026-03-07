# Anchor-binding Hardening Design Options (No S1 baseline changes)

## A) Capsule Builder: anchor extraction enhancement
**Idea**: extract and persist the frozen 7-anchor tuple per turn/segment.

- Expected improvements:
  - Better anchor completeness (decision/entity/time/constraint/open-loop/tool-state)
  - Less "correct topic, wrong anchor" failure
- Risks:
  - Over-extraction noise; contradictory anchors from long traces
  - Increased capsule size / token pressure
- Minimal verifiable experiment:
  - On micro-benchmark-12, run shadow extraction only
  - Measure anchor fill-rate per anchor type and conflict-rate
  - Success criterion: +25% decision/time anchor fill-rate without >10% conflict increase

## B) Retrieve: anchor-aware ranking
**Idea**: rerank candidate snippets by anchor match score (topic + anchor tuple overlap), not topic similarity alone.

- Expected improvements:
  - Higher precision in first retrieved snippet
  - Improved old-topic recovery for replay samples with dense history
- Risks:
  - Overfitting to sparse anchors; may hurt recall when anchors are missing
  - Bias toward recent but irrelevant anchor collisions
- Minimal verifiable experiment:
  - Replay micro-benchmark-12 with current retriever vs anchor-aware reranker
  - Compare top-1 anchor coverage and old_topic_recovery_on_scorable_samples
  - Success criterion: top-1 anchor coverage +20%, recovery +0.08 (absolute)

## C) Prompt Assemble: explicit anchor injection
**Idea**: inject a compact explicit "Anchor Block" (7 fields) into assembly context for downstream reasoning.

- Expected improvements:
  - Better adherence to constraints/open loops/tool state
  - Reduced stale-constraint and wrong-anchor cases
- Risks:
  - Prompt bloat / instruction interference
  - Model anchoring too hard on incomplete anchors
- Minimal verifiable experiment:
  - A/B on micro-benchmark-12 with identical retrieval, prompt-only change
  - Evaluate label shifts: wrong_anchor/tool_state_missing/open_loop_missing
  - Success criterion: these three labels combined reduced by >=30%

---

## Execution guardrails
- Do not modify S1 scoring/metrics/schema/baseline.
- Do not declare Gate 1 PASS/FAIL from this branch.
- Keep this line as parallel hardening only.
