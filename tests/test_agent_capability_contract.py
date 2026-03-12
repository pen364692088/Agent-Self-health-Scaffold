import json, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent.parent
CAP_DIR = W / 'artifacts' / 'self_health' / 'capabilities'
STATE = W / 'artifacts' / 'self_health' / 'state'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_capability_check_records_result():
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE/'heartbeat.status.json').write_text(json.dumps({'status':'ok','metrics':{}}))
    code, out, err = run([str(W/'tools'/'agent-capability-check'), '--capability', 'CAP-HEARTBEAT_CYCLE_EXECUTION', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert len(data) == 1
    assert data[0]['capability_id'] == 'CAP-HEARTBEAT_CYCLE_EXECUTION'
    assert data[0]['status'] in {'healthy', 'stale', 'degraded', 'missing', 'unknown', 'telemetry_missing'}
    assert (CAP_DIR/'CAP-HEARTBEAT_CYCLE_EXECUTION.json').exists()


def test_capability_check_all():
    for f in CAP_DIR.glob('CAP-*.json'):
        f.unlink()
    code, out, err = run([str(W/'tools'/'agent-capability-check'), '--all', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert len(data) >= 5


def test_capability_summary_aggregates():
    code, out, err = run([str(W/'tools'/'agent-capability-summary'), '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert 'total' in data
    assert 'by_status' in data
    assert 'degraded_capabilities' in data
