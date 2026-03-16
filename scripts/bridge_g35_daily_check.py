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
    """Generate metrics snapshot for the date with standardized format."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Standardized observation record format
    # All metrics MUST include value + numerator + denominator
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
            "adoption_rate": {"value": 0.0, "num": 0, "den": 0},
            "quality_improvement_rate": {"value": 0.0, "num": 0, "den": 0},
            "noise_rate": {"value": 0.0, "num": 0, "den": 0},
            "prompt_bloat_rate": {"value": 0.0, "num": 0, "den": 0},
            "rollback_after_recall": {"value": 0.0, "num": 0, "den": 0},
            "demote_after_recall": {"value": 0.0, "num": 0, "den": 0},
            "main_chain_success_rate": {"value": 1.0, "baseline_delta": 0.0},
            "fail_open_stability": {"value": 1.0, "num": 0, "den": 0},
        },
        "threshold_result": {
            "warning_triggered": [],
            "critical_triggered": [],
        },
        "anomalies": [],
        "status": "healthy",
        "summary": "No observation data collected yet. Awaiting first window.",
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


def check_alerts(metrics: dict) -> tuple[list, list]:
    """Check if any metrics exceed alert thresholds.
    
    Returns:
        tuple of (warning_triggered, critical_triggered)
    """
    warning_triggered = []
    critical_triggered = []
    
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
    
    # Check warning thresholds
    for metric, threshold in warning_thresholds.items():
        value_obj = metrics_data.get(metric, {"value": 0})
        value = value_obj.get("value", 0) if isinstance(value_obj, dict) else value_obj
        
        if metric in ["adoption_rate", "quality_improvement_rate"]:
            if value < threshold:
                warning_triggered.append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "direction": "below",
                })
        else:  # noise_rate, prompt_bloat_rate
            if value > threshold:
                warning_triggered.append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "direction": "above",
                })
    
    # Check critical thresholds
    for metric, threshold in critical_thresholds.items():
        value_obj = metrics_data.get(metric, {"value": 0})
        value = value_obj.get("value", 0) if isinstance(value_obj, dict) else value_obj
        
        if metric == "fail_open_stability":
            if value < threshold:
                critical_triggered.append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "direction": "below",
                })
        else:  # rollback_after_recall, demote_after_recall
            if value > threshold:
                critical_triggered.append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "direction": "above",
                })
    
    # Check main_chain_success_rate
    mcsr_obj = metrics_data.get("main_chain_success_rate", {"value": 1.0, "baseline_delta": 0.0})
    baseline_delta = mcsr_obj.get("baseline_delta", 0) if isinstance(mcsr_obj, dict) else 0
    
    if baseline_delta < 0:
        critical_triggered.append({
            "metric": "main_chain_success_rate",
            "value": mcsr_obj.get("value", 1.0),
            "threshold": "no decrease",
            "direction": "decreased",
            "delta": baseline_delta,
        })
    
    return warning_triggered, critical_triggered


def determine_status(warning_triggered: list, critical_triggered: list) -> str:
    """Determine observation window status."""
    if critical_triggered:
        return "critical-review-required"
    elif warning_triggered:
        return "warning"
    else:
        return "healthy"


def generate_summary(status: str, warning_triggered: list, critical_triggered: list) -> str:
    """Generate human-readable summary."""
    if status == "healthy":
        return "No warning or critical thresholds triggered in this window."
    elif status == "warning":
        metrics = [a["metric"] for a in warning_triggered]
        return f"Warning threshold(s) triggered: {', '.join(metrics)}. Continue observation."
    else:
        metrics = [a["metric"] for a in critical_triggered]
        return f"CRITICAL: Threshold(s) triggered: {', '.join(metrics)}. Immediate review required."


def format_report(metrics: dict, warning_triggered: list, critical_triggered: list) -> str:
    """Format report message."""
    date = metrics.get("_metadata", {}).get("date", "unknown")
    status = metrics.get("status", "unknown")
    summary = metrics.get("summary", "")
    
    lines = [
        f"📊 Bridge G3.5 Observation Report - {date}",
        "",
        f"Status: {status.upper()}",
        "",
        "Metrics:",
    ]
    
    # Add each metric with numerator/denominator
    for metric_name, metric_data in metrics.get("metrics", {}).items():
        if isinstance(metric_data, dict):
            value = metric_data.get("value", 0)
            num = metric_data.get("num", "N/A")
            den = metric_data.get("den", "N/A")
            
            if num != "N/A" and den != "N/A":
                lines.append(f"  • {metric_name}: {value:.2%} ({num}/{den})")
            elif "baseline_delta" in metric_data:
                lines.append(f"  • {metric_name}: {value:.2%} (delta: {metric_data['baseline_delta']:+.2%})")
            else:
                lines.append(f"  • {metric_name}: {value:.2%}")
    
    lines.extend([
        "",
        f"Sample Count: {metrics.get('sample_count', 0)}",
        "",
    ])
    
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
    warning_triggered, critical_triggered = check_alerts(metrics)
    metrics["threshold_result"]["warning_triggered"] = warning_triggered
    metrics["threshold_result"]["critical_triggered"] = critical_triggered
    
    # Determine status
    status = determine_status(warning_triggered, critical_triggered)
    metrics["status"] = status
    
    # Generate summary
    summary = generate_summary(status, warning_triggered, critical_triggered)
    metrics["summary"] = summary
    
    # Save metrics
    filepath = save_metrics(metrics, obs_dir)
    print(f"Metrics saved to: {filepath}")
    
    # Format report
    report = format_report(metrics, warning_triggered, critical_triggered)
    print(report)
    
    # Send report if requested
    if args.send_report:
        # Would integrate with OpenClaw message tool
        print("\n[Report would be sent to user via Telegram]")


if __name__ == "__main__":
    main()
