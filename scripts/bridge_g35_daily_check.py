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
    """Generate metrics snapshot for the date."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Placeholder metrics - would be collected from actual bridge
    # All observation records MUST include these 4 required fields:
    # 1. sample_count
    # 2. task_type_distribution
    # 3. window_start
    # 4. window_end
    metrics = {
        "date": date,
        "timestamp": timestamp,
        "sample_count": 0,  # REQUIRED: Number of requests/sessions
        "task_type_distribution": {  # REQUIRED: Breakdown by task type
            "coding": 0,
            "decision": 0,
            "question": 0,
        },
        "window_start": f"{date}T00:00:00-05:00",  # REQUIRED: Start of observation window
        "window_end": f"{date}T23:59:59-05:00",  # REQUIRED: End of observation window
        "metrics": {
            "adoption_rate": "TBD",
            "quality_improvement_rate": "TBD",
            "noise_rate": "TBD",
            "prompt_bloat_rate": "TBD",
            "rollback_after_recall": 0,
            "demote_after_recall": 0,
            "main_chain_success_rate": "TBD",
            "fail_open_stability": 1.0,
        },
        "counts": {
            "total_requests": 0,
            "total_suggestions": 0,
            "total_adoptions": 0,
            "total_errors": 0,
        },
        "anomalies": [],
        "alerts": [],
    }
    
    return metrics


def save_metrics(metrics: dict, obs_dir: Path) -> Path:
    """Save metrics to file."""
    filename = f"{metrics['date']}.json"
    filepath = obs_dir / filename
    
    with open(filepath, "w") as f:
        json.dump(metrics, f, indent=2)
    
    return filepath


def check_alerts(metrics: dict) -> list:
    """Check if any metrics exceed alert thresholds."""
    alerts = []
    
    thresholds = {
        "adoption_rate": (0.4, "below"),
        "quality_improvement_rate": (0.1, "below"),
        "noise_rate": (0.15, "above"),
        "prompt_bloat_rate": (0.25, "above"),
        "rollback_after_recall": (0.05, "above"),
        "demote_after_recall": (0.10, "above"),
        "fail_open_stability": (1.0, "below"),
    }
    
    for metric, (threshold, direction) in thresholds.items():
        value = metrics["metrics"].get(metric, "TBD")
        
        if value == "TBD":
            continue
        
        if direction == "below" and value < threshold:
            alerts.append({
                "metric": metric,
                "value": value,
                "threshold": threshold,
                "severity": "warning" if metric in ["adoption_rate", "quality_improvement_rate"] else "critical",
            })
        elif direction == "above" and value > threshold:
            alerts.append({
                "metric": metric,
                "value": value,
                "threshold": threshold,
                "severity": "warning" if metric in ["noise_rate", "prompt_bloat_rate"] else "critical",
            })
    
    return alerts


def format_report(metrics: dict, alerts: list) -> str:
    """Format report message."""
    date = metrics["date"]
    
    lines = [
        f"📊 Bridge G3.5 Observation Report - {date}",
        "",
        "Metrics Snapshot:",
        f"• Adoption Rate: {metrics['metrics']['adoption_rate']} (target: ≥40%)",
        f"• Quality Improvement: {metrics['metrics']['quality_improvement_rate']} (target: ≥10%)",
        f"• Noise Rate: {metrics['metrics']['noise_rate']} (target: ≤15%)",
        f"• Prompt Bloat: {metrics['metrics']['prompt_bloat_rate']} (target: ≤25%)",
        f"• Fail-Open Stability: {metrics['metrics']['fail_open_stability']} (target: 100%)",
        "",
        f"Total Requests: {metrics['counts']['total_requests']}",
        f"Total Suggestions: {metrics['counts']['total_suggestions']}",
        f"Total Adoptions: {metrics['counts']['total_adoptions']}",
        "",
    ]
    
    if alerts:
        lines.append("⚠️ Alerts:")
        for alert in alerts:
            lines.append(f"  • {alert['metric']}: {alert['value']} (threshold: {alert['threshold']})")
        lines.append("")
    
    lines.extend([
        "Status: 🔒 FROZEN (Observation Mode)",
        "Period: 2026-03-16 ~ 2026-03-30",
    ])
    
    return "\n".join(lines)


def main():
    args = parse_args()
    
    # Create observation directory
    obs_dir = create_observation_dir()
    
    # Generate metrics
    metrics = generate_metrics_snapshot(args.date)
    
    # Check alerts
    alerts = check_alerts(metrics)
    metrics["alerts"] = alerts
    
    # Save metrics
    filepath = save_metrics(metrics, obs_dir)
    print(f"Metrics saved to: {filepath}")
    
    # Format report
    report = format_report(metrics, alerts)
    print(report)
    
    # Send report if requested
    if args.send_report:
        # Would integrate with OpenClaw message tool
        print("\n[Report would be sent to user via Telegram]")


if __name__ == "__main__":
    main()
