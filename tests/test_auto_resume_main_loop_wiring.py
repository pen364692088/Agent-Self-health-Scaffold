import json
import os
import subprocess
from pathlib import Path

W = Path(os.environ.get('OPENCLAW_WORKSPACE', '/home/moonlight/.openclaw/workspace'))


def run(cmd):
    return subprocess.run(cmd, cwd=W, capture_output=True, text=True)


def test_scheduler_quick_includes_auto_resume_result():
    r = run([str(W / 'tools' / 'agent-self-health-scheduler'), '--mode', 'quick', '--force', '--json', '--no-probes'])
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert 'auto_resume' in data
    assert data['auto_resume']['status'] in {'ok', 'failed', 'error', 'unavailable'}
