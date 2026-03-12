import json, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent.parent
STATE = W / 'artifacts' / 'self_health' / 'state'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_snapshot_missing_probe_yields_insufficient_evidence_shape():
    marker = STATE/'heartbeat.status.json'
    if marker.exists():
        marker.unlink()
    code, out, err = run([str(W/'tools'/'agent-health-snapshot'), '--component', 'heartbeat', '--phase', 'before', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['snapshot']['component'] == 'heartbeat'
    assert 'missing_probe' in data['snapshot']['failure_indicators']


def test_recovery_verify_recovered(tmp_path):
    before = tmp_path/'before.json'
    after = tmp_path/'after.json'
    before.write_text(json.dumps({'status':'error','failure_indicators':['stale']}))
    after.write_text(json.dumps({'status':'ok','failure_indicators':[]}))
    code, out, err = run([str(W/'tools'/'agent-recovery-verify'), '--before', str(before), '--after', str(after), '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['verdict'] == 'recovered'
    assert data['rollback_needed'] is False


def test_self_heal_emits_recovery_record():
    STATE.mkdir(parents=True, exist_ok=True)
    for f in (W/'artifacts'/'self_health'/'recovery_logs').glob('recovery_*.json'):
        f.unlink()
    (STATE/'health_check.status.json').write_text(json.dumps({'status':'warning','key_metrics':{'lag':10},'failure_indicators':['stale']}))
    code, out, err = run([str(W/'tools'/'agent-self-heal'), '--action', 'rotate_logs', '--component', 'health_check', '--json'])
    assert code == 0, err
    data = json.loads(out)
    assert data['recovery_id'].startswith('REC-')
    assert data['snapshot_before_path']
    assert data['snapshot_after_path']
    assert data['verdict'] in {'recovered','unchanged','degraded','insufficient_evidence'}
