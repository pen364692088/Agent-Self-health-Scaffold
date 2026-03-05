#!/usr/bin/env python3

from pathlib import Path

from openviking.ops.alerting import Alert, AlertManager


def test_alert_dedupe_and_cooldown(tmp_path):
    mgr = AlertManager(
        state_path=tmp_path / 'alert_state.json',
        failed_dir=tmp_path / 'failed',
        cooldown_warn_sec=3600,
        cooldown_error_sec=600,
        webhook_url=None,
    )

    a1 = Alert(
        level='WARN',
        rule_id='rule_x',
        root_uri='viking://resources/user/memory/',
        reason_signature='r1',
        message='warn once',
    )

    r1 = mgr.send(a1)
    assert r1['fingerprint']

    # same alert immediately should be blocked by cooldown
    ok2, reason2 = mgr.should_send(a1)
    assert ok2 is False
    assert reason2 == 'cooldown_active'
