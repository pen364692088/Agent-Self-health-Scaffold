import json, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent.parent
REC = W / 'artifacts' / 'self_health' / 'recovery_logs'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def setup_recovery_log(name, data):
    REC.mkdir(parents=True, exist_ok=True)
    (REC / f'recovery_{name}').write_text(json.dumps(data))


def test_evidence_actions_excluded_from_recovery_rate():
    for f in REC.glob('recovery_*.json'):
        f.unlink()
    setup_recovery_log('rec_001.json', {
        'recovery_id': 'REC-001', 'action': 'rerun_health_check', 'component': 'heartbeat',
        'started_at': '2026-03-08T12:00:00Z', 'verdict': 'recovered',
        'action_result': {'kind': 'evidence_refresh', 'counts_as_recovery': False},
        'precondition_status': 'met', 'escalation_state': 'none', 'guard': {}
    })
    setup_recovery_log('rec_002.json', {
        'recovery_id': 'REC-002', 'action': 'restart_worker', 'component': 'callback-worker',
        'started_at': '2026-03-08T12:05:00Z', 'verdict': 'recovered',
        'action_result': {}, 'precondition_status': 'met', 'escalation_state': 'none', 'guard': {}
    })
    code, out, err = run([str(W/'tools'/'agent-recovery-summary'), '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['evidence_actions_total'] == 1
    assert data['recovery_actions_total'] == 1
    assert data['direct_recovery_total'] == 1
    assert abs(data['recovery_effective_rate'] - 1.0) < 1e-6


def test_clear_stale_lock_details_not_conflated():
    for f in REC.glob('recovery_*.json'):
        f.unlink()
    setup_recovery_log('rec_003.json', {
        'recovery_id': 'REC-003', 'action': 'clear_stale_lock', 'component': 'mailbox-worker',
        'started_at': '2026-03-08T12:10:00Z', 'verdict': 'unchanged',
        'action_result': {'lock_removed': True, 'downstream_progress_resumed': False},
        'precondition_status': 'met', 'escalation_state': 'none', 'guard': {}
    })
    code, out, err = run([str(W/'tools'/'agent-recovery-summary'), '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['clear_stale_lock_details']['lock_removed'] == 1
    assert data['clear_stale_lock_details']['recovery_confirmed'] == 0


def test_top_flaky_components_identified():
    for f in REC.glob('recovery_*.json'):
        f.unlink()
    setup_recovery_log('rec_004.json', {
        'recovery_id': 'REC-004', 'action': 'restart_worker', 'component': 'callback-worker',
        'started_at': '2026-03-08T12:15:00Z', 'verdict': 'degraded',
        'action_result': {}, 'precondition_status': 'met', 'escalation_state': 'none', 'guard': {}
    })
    code, out, err = run([str(W/'tools'/'agent-recovery-summary'), '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert any(c['component'] == 'callback-worker' for c in data['top_flaky_components'])
