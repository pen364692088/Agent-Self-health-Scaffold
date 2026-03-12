#!/usr/bin/env python3
import json, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent.parent

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def test_health_endpoints():
    for tool in ['agent-health-check','agent-health-summary','agent-incident-report','agent-self-heal']:
        code,out,err = run([str(W/'tools'/tool), '--health'])
        assert code == 0, (tool, err)
        data=json.loads(out)
        assert data['status']=='healthy'

def test_health_check_and_summary_json():
    code,out,err = run([str(W/'tools'/'agent-health-check'), '--deep', '--json'])
    assert code in (0,1,2,3)
    data=json.loads(out)
    assert 'overall_status' in data
    assert 'components' in data and len(data['components']) >= 4
    code,out,err = run([str(W/'tools'/'agent-health-summary'), '--json'])
    assert code in (0,1,2,3)
    data=json.loads(out)
    assert 'current_level' in data

def test_incident_create_and_self_heal_proposal():
    code,out,err = run([str(W/'tools'/'agent-incident-report'), '--level', 'YELLOW', '--category', 'subagent', '--summary', 'test incident', '--json'])
    assert code == 0, err
    data=json.loads(out)
    assert data['incident_id'].startswith('INC-')
    code,out,err = run([str(W/'tools'/'agent-self-heal'), '--proposal-only', '--action', 'restart_subsystem', '--level', 'B', '--json'])
    assert code == 0, err
    data=json.loads(out)
    assert data['status'] == 'pending_review'
