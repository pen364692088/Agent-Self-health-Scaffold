# Runtime Default Discovery

**Discovered**: 2026-03-08T00:17:00-06:00

---

## Discovery Method

Analyzed actual compression event and model config to determine runtime truth.

---

## Runtime Truth (Observed)

### Model Configuration
```json
{
  "model": "openai-codex/gpt-5.4",
  "contextWindow": 200000,
  "maxTokens": 32768,
  "provider": "openai-codex"
}
```

### Compression Behavior
```json
{
  "trigger_type": "threshold_92",
  "before_ratio": 1.0209,
  "after_ratio": 0.6125,
  "mode": "enforced"
}
```

### Inferred Thresholds
```
threshold_strong: 0.92 (observed trigger point)
threshold_enforced: NOT YET OBSERVED at 0.85
```

---

## Documented Target (Not Yet in Effect)

```json
{
  "max_tokens": 100000,
  "threshold_enforced": 0.85,
  "threshold_strong": 0.92
}
```

---

## Gap Analysis

| Parameter | Runtime Truth | Target Policy | Gap |
|-----------|---------------|---------------|-----|
| Context Window | 200k | 100k | 2x larger |
| Trigger Point | 0.92+ | 0.85 | Later trigger |
| Pre-assemble | Not observed | Required | Unknown |

---

## Implications

1. **Current natural evidence proves**: Compression works at `200k / 0.92`
2. **Does NOT prove**: `100k / 0.85` policy is active
3. **Milestone B must be split**: B1 (runtime truth) + B2 (policy compliance)

---

*Discovery recorded: 2026-03-08T00:17:00-06:00*
