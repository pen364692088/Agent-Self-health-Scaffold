# Automated Monitoring Plan

## Metadata
- **Phase**: C - Automated Monitoring Enhancement
- **Date**: 2026-03-09
- **Version**: V3 (2.1-decision-context-enhanced)

---

## Current State

### Minimal Viable Monitoring (Already in Place)

| Item | Status | Implementation |
|------|--------|----------------|
| Version logging | ✅ | evaluator_version in capsule |
| Gate logging | ✅ | v2_gates in evaluation |
| Baseline metrics | ✅ | Agreement 92%, FP 7% |
| Rollback path | ✅ | --v2 flag in wrapper |

### Gaps

| Gap | Risk | Priority |
|-----|------|----------|
| No auto-sampling | Can't detect drift early | HIGH |
| No per-bucket watch | May miss bucket-specific issues | HIGH |
| No trend tracking | Can't see degradation over time | MEDIUM |
| No automated alerts | Issues may go unnoticed | MEDIUM |
| Create action ambiguity tracking | P2 issue not monitored | LOW |

---

## Monitoring Enhancement Plan

### 1. Auto-Sampling Shadow Traces

**Purpose**: Periodically sample and validate evaluator output.

**Implementation**:
```
tools/monitor-shadow-sampler
  --interval 1h
  --sample-size 10
  --output artifacts/monitoring/shadow_samples/
```

**Output**:
```json
{
  "timestamp": "2026-03-09T13:00:00",
  "sample_id": "shadow_sample_20260309_130000",
  "readiness": 0.85,
  "decision_context": {...},
  "spot_check_required": false
}
```

**Frequency**: Every hour
**Sample Size**: 10 capsules
**Alert**: If spot_check_required = true

---

### 2. Per-Bucket Agreement/FP Watch

**Purpose**: Track agreement and FP rate per bucket.

**Implementation**:
```
tools/monitor-bucket-metrics
  --bucket long_technical,real_main_agent,historical
  --window 24h
  --output artifacts/monitoring/bucket_metrics.json
```

**Output**:
```json
{
  "timestamp": "2026-03-09T13:00:00",
  "buckets": {
    "long_technical": {
      "samples": 15,
      "agreement": 1.0,
      "fp_rate": 0.0,
      "dc_coverage": 1.0,
      "status": "healthy"
    },
    "real_main_agent": {
      "samples": 30,
      "agreement": 0.93,
      "fp_rate": 0.07,
      "dc_coverage": 0.67,
      "status": "healthy"
    }
  }
}
```

**Alert Thresholds**:
- Agreement < 80%
- FP Rate > 20%
- DC Coverage < 50%

---

### 3. Decision Context Coverage Trend

**Purpose**: Track DC extraction coverage over time.

**Implementation**:
```
tools/monitor-dc-trend
  --window 7d
  --output artifacts/monitoring/dc_trend.json
```

**Output**:
```json
{
  "timestamp": "2026-03-09T13:00:00",
  "window": "7d",
  "dc_coverage_trend": [0.80, 0.85, 0.90, 0.95, 1.0, 1.0, 1.0],
  "current_coverage": 1.0,
  "trend": "stable",
  "drift_detected": false
}
```

**Alert**:
- Coverage drops > 20% from baseline
- Trend shows consistent decline

---

### 4. Create Action Ambiguity Tracking

**Purpose**: Monitor P2 issue (create action ambiguity).

**Implementation**:
```
tools/monitor-create-action-ambiguity
  --output artifacts/monitoring/create_ambiguity.json
```

**Output**:
```json
{
  "timestamp": "2026-03-09T13:00:00",
  "create_action_samples": 5,
  "ambiguous_count": 1,
  "ambiguity_rate": 0.20,
  "impact_rate": 0.0,
  "status": "watch"
}
```

**Priority**: LOW (P2 issue)
**Alert**: If impact_rate > 10%

---

### 5. Recent-Window Drift Alert

**Purpose**: Detect drift in recent samples.

**Implementation**:
```
tools/monitor-drift-watch
  --window 24h
  --compare-to baseline
  --output artifacts/monitoring/drift_watch.json
```

**Output**:
```json
{
  "timestamp": "2026-03-09T13:00:00",
  "window": "24h",
  "metrics": {
    "agreement": {"current": 0.95, "baseline": 0.92, "delta": +0.03},
    "fp_rate": {"current": 0.05, "baseline": 0.07, "delta": -0.02},
    "dc_coverage": {"current": 1.0, "baseline": 1.0, "delta": 0.0}
  },
  "drift_detected": false,
  "alerts": []
}
```

**Alert Thresholds**:
- Any metric delta > |10%|
- Consistent decline over 3 windows

---

## Dashboard

### Metrics to Display

| Metric | Current | Baseline | Alert | Trend |
|--------|---------|----------|-------|-------|
| Agreement | 92% | 92% | < 80% | - |
| FP Rate | 7% | 7% | > 20% | - |
| DC Coverage | 100% | 100% | < 50% | - |
| Outcome (partial+) | 100% | 100% | < 70% | - |

### Location

```
artifacts/monitoring/DASHBOARD.md (auto-generated)
```

---

## Implementation Priority

| Item | Priority | Effort | Value |
|------|----------|--------|-------|
| Auto-sampling | HIGH | Medium | High |
| Per-bucket watch | HIGH | Medium | High |
| DC trend tracking | MEDIUM | Low | Medium |
| Drift alert | MEDIUM | Low | Medium |
| Create ambiguity tracking | LOW | Low | Low |

**Recommended Order**:
1. Auto-sampling + Per-bucket watch (parallel)
2. DC trend + Drift alert (parallel)
3. Create ambiguity tracking (later)

---

## Rollout Plan

### Week 1
- Implement auto-sampling
- Implement per-bucket watch
- Collect baseline data

### Week 2
- Implement DC trend tracking
- Implement drift alert
- Set up dashboard

### Week 3+
- Monitor and tune thresholds
- Add more signals as needed
- Integrate with heartbeat if needed

---

*Monitoring Plan v1.0*
*Phase C: Automated Monitoring Enhancement*
