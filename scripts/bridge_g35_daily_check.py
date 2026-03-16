#!/usr/bin/env python3
"""
Bridge G3.5 Daily Check Script

Collects metrics and generates daily observation report.

Usage:
    python scripts/bridge_g35_daily_check.py --date YYYY-MM-DD [--send-report]
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path("/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold")
ARTIFACTS_DIR = PROJECT_DIR / "artifacts" / "memory"


def parse_args():
    parser = argparse.ArgumentParser(description="Bridge G3.5 Daily Check")
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    parser.add_argument("--send-report", action="store_true", help="Send report to user")
    return parser.parse_args()


def create_observation_dir():
    """Create observation directory if not exists."""
    obs_dir = ARTIFACTS_DIR / "bridge_g35_observations"
    obs_dir.mkdir(parents=True, exist_ok=True)
    return obs_dir


def generate_metrics_snapshot(date: str) -> dict:
    """Generate metrics snapshot for the date with standardized format.
    
    When sample_count = 0 or den = 0, metrics are marked as not_evaluable.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Standardized observation record format
    # All metrics MUST include value + numerator + denominator
    # When sample_count = 0, status = "insufficient_evidence"
    metrics = {
        "window_start": f"{date}T00:00:00-05:00",
        "window_end": f"{date}T23:59:59-05:00",
        "sample_count": 0,
        "task_type_distribution": {
            "coding": 0,
            "decision": 0,
            "question": 0,
        },
        "metrics": {
            "adoption_rate": {"value": None, "num": 0, "den": 0},
            "quality_improvement_rate": {"value": None, "num": 0, "den": 0},
            "noise_rate": {"value": None, "num": 0, "den": 0},
            "prompt_bloat_rate": {"value": None, "num": 0, "den": 0},
            "rollback_after_recall": {"value": None, "num": 0, "den": 0},
            "demote_after_recall": {"value": None, "num": 0, "den": 0},
            "main_chain_success_rate": {"value": None, "baseline_delta": None},
            "fail_open_stability": {"value": None, "num": 0, "den": 0},
        },
        "threshold_result": {
            "warning_triggered": [],
            "critical_triggered": [],
            "not_evaluable": [
                "adoption_rate",
                "quality_improvement_rate",
                "noise_rate",
                "prompt_bloat_rate",
                "rollback_after_recall",
                "demote_after_recall",
                "main_chain_success_rate",
                "fail_open_stability",
            ],
        },
        "anomalies": [],
        "status": "insufficient_evidence",
        "summary": "Observation period started. No eligible samples collected in this window yet.",
        "_metadata": {
            "date": date,
            "timestamp": timestamp,
        },
    }
    
    return metrics


def save_metrics(metrics: dict, obs_dir: Path) -> Path:
    """Save metrics to file."""
    filename = f"{metrics['date']}.json"
    filepath = obs_dir / filename
    
    with open(filepath, "w") as f:
        json.dump(metrics, f, indent=2)
    
    return filepath


def check_alerts(metrics: dict) -> tuple[list, list, list]:
    """Check if any metrics exceed alert thresholds.
    
    Returns:
        tuple of (warning_triggered, critical_triggered, not_evaluable)
    
    Note: When sample_count = 0 or den = 0, metric is not_evaluable
          and should not be counted toward healthy/warning/critical.
    """
    warning_triggered = []
    critical_triggered = []
    not_evaluable = []
    
    # Warning thresholds
    warning_thresholds = {
        "adoption_rate": 0.4,  # < 40%
        "quality_improvement_rate": 0.1,  # < 10%
        "noise_rate": 0.15,  # > 15%
        "prompt_bloat_rate": 0.25,  # > 25%
    }
    
    # Critical thresholds
    critical_thresholds = {
        "rollback_after_recall": 0.05,  # > 5%
        "demote_after_recall": 0.10,  # > 10%
        "fail_open_stability": 1.0,  # < 100%
    }
    
    metrics_data = metrics.get("metrics", {})
    sample_count = metrics.get("sample_count", 0)
    
    # If sample_count = 0, all metrics are not_evaluable
    if sample_count == 0:
        not_evaluable = list(metrics_data.keys())
        return warning_triggered, critical_triggered, not_evaluable
    
    # Check warning thresholds
    for metric, threshold in warning_thresholds.items():
        value_obj = metrics_data.get(metric, {"value": None})
        value = value_obj.get("value") if isinstance(value_obj, dict) else None
        num = value_obj.get("num", 0) if isinstance(value_obj, dict) else 0
        den = value_obj.get("den", 0) if isinstance(value_obj, dict) else 0
        
        # Check if evaluable
        if value is None or den == 0:
            not_evaluable.append(metric)
            continue
        
        if metric in ["adoption_rate", "quality_improvement_rate"]:
            if value < threshold:
                warning_triggered.append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "direction": "below",
                    "num": num,
                    "den": den,
                })
        else:  # noise_rate, prompt_bloat_rate
            if value > threshold:
                warning_triggered.append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "direction": "above",
                    "num": num,
                    "den": den,
                })
    
    # Check critical thresholds
    for metric, threshold in critical_thresholds.items():
        value_obj = metrics_data.get(metric, {"value": None})
        value = value_obj.get("value") if isinstance(value_obj, dict) else None
        num = value_obj.get("num", 0) if isinstance(value_obj, dict) else 0
        den = value_obj.get("den", 0) if isinstance(value_obj, dict) else 0
        
        # Check if evaluable
        if value is None or (metric != "main_chain_success_rate" and den == 0):
            not_evaluable.append(metric)
            continue
        
        if metric == "fail_open_stability":
            if value < threshold:
                critical_triggered.append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "direction": "below",
                    "num": num,
                    "den": den,
                })
        else:  # rollback_after_recall, demote_after_recall
            if value > threshold:
                critical_triggered.append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "direction": "above",
                    "num": num,
                    "den": den,
                })
    
    # Check main_chain_success_rate
    mcsr_obj = metrics_data.get("main_chain_success_rate", {"value": None, "baseline_delta": None})
    baseline_delta = mcsr_obj.get("baseline_delta") if isinstance(mcsr_obj, dict) else None
    
    if baseline_delta is None:
        not_evaluable.append("main_chain_success_rate")
    elif baseline_delta < 0:
        critical_triggered.append({
            "metric": "main_chain_success_rate",
            "value": mcsr_obj.get("value"),
            "threshold": "no decrease",
            "direction": "decreased",
            "delta": baseline_delta,
        })
    
    return warning_triggered, critical_triggered, not_evaluable


def determine_status(sample_count: int, warning_triggered: list, critical_triggered: list, not_evaluable: list) -> str:
    """Determine observation window status.
    
    Priority:
    1. insufficient_evidence: sample_count = 0
    2. provisional: 0 < sample_count < MIN_SAMPLE_THRESHOLD
    3. critical-review-required: critical thresholds triggered
    4. warning: warning thresholds triggered
    5. healthy: no thresholds triggered (with sufficient samples)
    
    MIN_SAMPLE_THRESHOLD = 5
    Small samples can produce misleading "100%" or "0%" rates.
    """
    MIN_SAMPLE_THRESHOLD = 5
    
    # If no samples, status is insufficient_evidence
    if sample_count == 0:
        return "insufficient_evidence"
    
    # If too few samples, status is provisional (not healthy!)
    # Small samples can produce misleading perfect scores
    if sample_count < MIN_SAMPLE_THRESHOLD:
        return "provisional"
    
    if critical_triggered:
        return "critical-review-required"
    elif warning_triggered:
        return "warning"
    else:
        return "healthy"


def generate_summary(status: str, sample_count: int, warning_triggered: list, critical_triggered: list, not_evaluable: list) -> str:
    """Generate human-readable summary."""
    if status == "insufficient_evidence":
        return f"Observation period active. No eligible samples collected in this window (sample_count={sample_count})."
    elif status == "provisional":
        return f"Provisional status: sample_count={sample_count} (< 5). Too few samples for reliable metrics. Continue observation."
    elif status == "healthy":
        return "No warning or critical thresholds triggered in this window."
    elif status == "warning":
        metrics = [a["metric"] for a in warning_triggered]
        return f"Warning threshold(s) triggered: {', '.join(metrics)}. Continue observation."
    else:
        metrics = [a["metric"] for a in critical_triggered]
        return f"CRITICAL: Threshold(s) triggered: {', '.join(metrics)}. Immediate review required."


def format_report(metrics: dict, warning_triggered: list, critical_triggered: list, not_evaluable: list) -> str:
    """Format report message."""
    date = metrics.get("_metadata", {}).get("date", "unknown")
    status = metrics.get("status", "unknown")
    summary = metrics.get("summary", "")
    sample_count = metrics.get("sample_count", 0)
    
    lines = [
        f"📊 Bridge G3.5 Observation Report - {date}",
        "",
        f"Status: {status.upper()}",
        f"Sample Count: {sample_count}",
        "",
        "Metrics:",
    ]
    
    # Add each metric with numerator/denominator
    for metric_name, metric_data in metrics.get("metrics", {}).items():
        if isinstance(metric_data, dict):
            value = metric_data.get("value")
            num = metric_data.get("num", 0)
            den = metric_data.get("den", 0)
            
            if value is None:
                lines.append(f"  • {metric_name}: not_evaluable (den=0)")
            elif num != "N/A" and den != "N/A" and den > 0:
                lines.append(f"  • {metric_name}: {value:.2%} ({num}/{den})")
            elif "baseline_delta" in metric_data and metric_data["baseline_delta"] is not None:
                lines.append(f"  • {metric_name}: {value:.2%} (delta: {metric_data['baseline_delta']:+.2%})")
            else:
                lines.append(f"  • {metric_name}: not_evaluable")
    
    lines.append("")
    
    if not_evaluable:
        lines.append(f"ℹ️ Not Evaluable: {', '.join(not_evaluable)}")
        lines.append("")
    
    if warning_triggered:
        lines.append("⚠️ Warning Triggered:")
        for alert in warning_triggered:
            lines.append(f"  • {alert['metric']}: {alert['value']:.2%} (threshold: {alert['threshold']:.2%})")
        lines.append("")
    
    if critical_triggered:
        lines.append("🔴 Critical Triggered:")
        for alert in critical_triggered:
            lines.append(f"  • {alert['metric']}: {alert.get('value', 'N/A')} (threshold: {alert['threshold']})")
        lines.append("")
    
    lines.extend([
        f"Summary: {summary}",
        "",
        "Period: 2026-03-16 ~ 2026-03-30 America/Winnipeg",
    ])
    
    return "\n".join(lines)


def main():
    args = parse_args()
    
    # Create observation directory
    obs_dir = create_observation_dir()
    
    # Generate metrics
    metrics = generate_metrics_snapshot(args.date)
    
    # Check alerts
    warning_triggered, critical_triggered, not_evaluable = check_alerts(metrics)
    metrics["threshold_result"]["warning_triggered"] = warning_triggered
    metrics["threshold_result"]["critical_triggered"] = critical_triggered
    metrics["threshold_result"]["not_evaluable"] = not_evaluable
    
    # Determine status
    sample_count = metrics.get("sample_count", 0)
    status = determine_status(sample_count, warning_triggered, critical_triggered, not_evaluable)
    metrics["status"] = status
    
    # Generate summary
    summary = generate_summary(status, sample_count, warning_triggered, critical_triggered, not_evaluable)
    metrics["summary"] = summary
    
    # Save metrics
    filepath = save_metrics(metrics, obs_dir)
    print(f"Metrics saved to: {filepath}")
    
    # Format report
    report = format_report(metrics, warning_triggered, critical_triggered, not_evaluable)
    print(report)
    
    # Send report if requested
    if args.send_report:
        # Would integrate with OpenClaw message tool
        print("\n[Report would be sent to user via Telegram]")


if __name__ == "__main__":
    main()
