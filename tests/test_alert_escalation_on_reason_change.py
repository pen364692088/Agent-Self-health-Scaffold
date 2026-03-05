#!/usr/bin/env python3

from openviking.ops.alerting import Alert, AlertManager


def test_alert_escalation_on_reason_change(tmp_path):
    mgr = AlertManager(
        state_path=tmp_path / 'alert_state.json',
        failed_dir=tmp_path / 'failed',
        cooldown_warn_sec=3600,
        cooldown_error_sec=600,
        webhook_url=None,
    )

    base = Alert(
        level='WARN',
        rule_id='coverage_min',
        root_uri='viking://resources/user/memory/',
        reason_signature='coverage=0.89',
        message='coverage warn',
    )
    mgr.send(base)

    changed = Alert(
        level='WARN',
        rule_id='coverage_min',
        root_uri='viking://resources/user/memory/',
        reason_signature='coverage=0.70',
        message='coverage worsened',
    )
    ok, reason = mgr.should_send(changed)
    assert ok is True
    assert reason == 'reason_changed'
