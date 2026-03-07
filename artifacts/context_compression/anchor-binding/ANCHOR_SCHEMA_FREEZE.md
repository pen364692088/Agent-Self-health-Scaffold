# Anchor Schema Freeze (S1 baseline frozen)

Status: **Frozen for parallel hardening line**
Constraint: Do **not** modify scoring/metrics/schema/baseline in S1 mainline.

Canonical anchors:
- `topic_key`
- `decision_anchor`
- `entity_anchor`
- `time_anchor`
- `constraint_anchor`
- `open_loop_anchor`
- `tool_state_anchor`

Notes:
- This is a design freeze artifact for branch `anchor-binding-hardening`.
- Any experiment must map outputs to these seven anchors.
