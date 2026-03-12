from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_PATHS = [
    ROOT / 'core' / 'task_ledger.py',
    ROOT / 'core' / 'reconciler',
    ROOT / 'runtime' / 'recovery-orchestrator',
    ROOT / 'runtime' / 'restart_executor',
    ROOT / 'runtime' / 'transcript_rebuilder',
    ROOT / 'runtime' / 'job_orchestrator',
    ROOT / 'pipelines' / 'gate-runner',
    ROOT / 'docs' / 'ARCHITECTURE.md',
    ROOT / 'schemas' / 'ledger-event.schema.json',
]


def test_v2_scaffold_paths_exist():
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED_PATHS if not p.exists()]
    assert not missing, f"Missing scaffold paths: {missing}"
