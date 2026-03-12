import json, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent.parent
CAP_DIR = W / 'artifacts' / 'self_health' / 'capabilities'
STATE = W / 'artifacts' / 'self_health' / 'state'
PROP_DIR = W / 'artifacts' / 'self_health' / 'proposals'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_forgetting_guard_detects_stale():
    CAP_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime, timezone, timedelta
    old_time = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    (CAP_DIR/'CAP-TEST_STALE.json').write_text(json.dumps({
        'capability_id': 'CAP-TEST_STALE',
        'status': 'healthy',
        'checked_at': old_time,
        'severity_if_missing': 'medium',
    }))
    code, out, err = run([str(W/'tools'/'agent-forgetting-guard'), '--capability', 'CAP-TEST_STALE', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert any(a['type'] == 'stale_verification' for a in data['alerts'])


def test_proposal_generation():
    for f in PROP_DIR.glob('PROP-*.json'):
        f.unlink()
    code, out, err = run([
        str(W/'tools'/'agent-generate-proposal'),
        '--type', 'timeout_adjustment',
        '--component', 'test-component',
        '--problem', 'Test problem',
        '--proposed-change', 'Increase timeout',
        '--rollback', 'Revert to old timeout',
        '--json'
    ])
    assert code == 0, err
    data = json.loads(out)
    assert data['proposal_only'] is True
    assert data['approval_required'] is True
    assert data['status'] == 'pending'


def test_proposal_summary():
    code, out, err = run([str(W/'tools'/'agent-proposal-summary'), '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert 'total' in data
    assert 'by_type' in data
