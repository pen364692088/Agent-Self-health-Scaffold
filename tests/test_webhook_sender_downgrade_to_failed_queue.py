#!/usr/bin/env python3

from pathlib import Path

from openviking.ops.alerting import Alert, AlertManager


def test_webhook_sender_downgrade_to_failed_queue(tmp_path):
    mgr = AlertManager(
        state_path=tmp_path / 'alert_state.json',
        failed_dir=tmp_path / 'failed',
        webhook_url='http://127.0.0.1:1/not-listening',
        cooldown_warn_sec=1,
        cooldown_error_sec=1,
    )

    alert = Alert(
        level='ERROR',
        rule_id='webhook_test',
        root_uri='viking://resources/user/memory/',
        reason_signature='network_down',
        message='should queue failed',
    )

    result = mgr.send(alert)
    assert result['sent'] is False
    assert result['reason'] == 'queued_failed_delivery'

    queued = list((tmp_path / 'failed').glob('*.json'))
    assert len(queued) >= 1
