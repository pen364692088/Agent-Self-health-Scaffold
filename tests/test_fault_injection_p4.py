import json, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent.parent
STATE = W / 'artifacts' / 'self_health' / 'state'
RUNTIME = W / 'artifacts' / 'self_health' / 'runtime'
CAP_DIR = W / 'artifacts' / 'self_health' / 'capabilities'
INC_DIR = W / 'artifacts' / 'self_health' / 'capability_incidents'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def clear_telemetry():
    """Clear telemetry files to simulate missing telemetry"""
    for f in RUNTIME.glob('*.json'):
        f.unlink()


def clear_state():
    for f in STATE.glob('*.json'):
        f.unlink()
    for f in CAP_DIR.glob('*.json'):
        f.unlink()
    for f in INC_DIR.glob('*.json'):
        f.unlink()


def test_fault_heartbeat_no_telemetry():
    """Fault injection: heartbeat telemetry missing"""
    clear_telemetry()
    
    code, out, err = run([str(W/'tools'/'agent-capability-check'), '--capability', 'CAP-HEARTBEAT_CYCLE_EXECUTION', '--json'])
    assert code == 0
    data = json.loads(out)
    # Without telemetry, should report telemetry_missing
    assert data[0]['status'] == 'telemetry_missing'


def test_fault_mailbox_stuck_via_telemetry():
    """Fault injection: mailbox stuck with no progress via telemetry"""
    clear_state()
    RUNTIME.mkdir(parents=True, exist_ok=True)
    # Create telemetry showing stuck worker
    (RUNTIME/'mailbox_worker_status.json').write_text(json.dumps({
        'worker_name': 'mailbox-worker',
        'alive': True,
        'last_poll_at': '2026-03-08T10:00:00Z',
        'last_progress_at': '2026-03-08T10:00:00Z',
        'backlog_count': 15,
        'stuck_suspected': True,
        'mailbox_status': 'warning'
    }))
    
    code, out, err = run([str(W/'tools'/'agent-capability-check'), '--capability', 'CAP-MAILBOX_CONSUMPTION', '--json'])
    assert code == 0
    data = json.loads(out)
    # With stuck telemetry, should report degraded
    assert data[0]['status'] == 'degraded'


def test_fault_forgetting_guard_detects_stale():
    """Fault injection: forgetting guard detects stale capability"""
    clear_state()
    CAP_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime, timezone, timedelta
    old_time = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    (CAP_DIR/'CAP-HEARTBEAT_CYCLE_EXECUTION.json').write_text(json.dumps({
        'capability_id': 'CAP-HEARTBEAT_CYCLE_EXECUTION',
        'status': 'healthy',
        'checked_at': old_time,
        'severity_if_missing': 'critical'
    }))
    
    code, out, err = run([str(W/'tools'/'agent-forgetting-guard'), '--capability', 'CAP-HEARTBEAT_CYCLE_EXECUTION', '--json'])
    assert code == 0
    data = json.loads(out)
    assert len(data['alerts']) > 0
    assert any(a['type'] == 'stale_verification' for a in data['alerts'])


def test_fault_proposal_dedup():
    """Fault injection: duplicate proposals are suppressed"""
    # Generate first proposal
    code, out1, err = run([
        str(W/'tools'/'agent-generate-proposal'),
        '--type', 'timeout_adjustment',
        '--component', 'test-dedup-p46',
        '--problem', 'Same problem',
        '--proposed-change', 'Same fix',
        '--rollback', 'Same rollback',
        '--json'
    ])
    assert code == 0
    data1 = json.loads(out1)
    
    # Try to generate duplicate
    code, out2, err = run([
        str(W/'tools'/'agent-generate-proposal'),
        '--type', 'timeout_adjustment',
        '--component', 'test-dedup-p46',
        '--problem', 'Same problem',
        '--proposed-change', 'Same fix',
        '--rollback', 'Same rollback',
        '--json'
    ])
    assert code == 0
    data2 = json.loads(out2)
    
    # Should have same proposal_id but suppressed_count increased
    assert data1['proposal_id'] == data2['proposal_id']
    assert data2.get('suppressed_count', 0) >= 1


def test_fault_gate_with_telemetry():
    """Fault injection: gate validates with telemetry"""
    code, out, err = run([str(W/'tools'/'gate-self-health-check'), '--json'])
    assert code == 0
    data = json.loads(out)
    # Gate should pass with telemetry integration
    assert data['gate_a']['status'] == 'PASS'
    assert data['gate_b']['status'] == 'PASS'
    assert data['gate_c']['status'] == 'PASS'
