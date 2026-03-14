from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools' / 'materialize-state'
SCHEMA = ROOT / 'schemas' / 'materialized_state.v0.schema.json'
FIX = ROOT / 'tests' / 'fixtures' / 'materialized_state'
ARTIFACT_TMP = ROOT / 'artifacts' / 'test_tmp' / 'materialized_state_contract'


def run_tool(session_state: Path, working_buffer: Path, output: Path):
    cmd = [
        sys.executable,
        str(TOOL),
        '--session-state', str(session_state),
        '--working-buffer', str(working_buffer),
        '--output', str(output),
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def normalize_dynamic(obj: dict) -> dict:
    obj = json.loads(json.dumps(obj))
    obj['derived_at'] = '__DYNAMIC__'
    return obj


def artifact_out(tmp_path: Path, name: str) -> Path:
    out_dir = ARTIFACT_TMP / tmp_path.name
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / name


def test_materialized_state_matches_golden_fixture(tmp_path: Path):
    out = artifact_out(tmp_path, 'golden.json')
    result = run_tool(
        FIX / 'session_state_fixture.md',
        FIX / 'working_buffer_fixture.md',
        out,
    )
    assert result.returncode == 0, result.stderr

    actual = normalize_dynamic(load_json(out))
    golden = load_json(FIX / 'golden_latest.json')
    assert actual == golden


def test_materialized_state_validates_against_json_schema(tmp_path: Path):
    out = artifact_out(tmp_path, 'schema.json')
    result = run_tool(
        FIX / 'session_state_fixture.md',
        FIX / 'working_buffer_fixture.md',
        out,
    )
    assert result.returncode == 0, result.stderr

    schema = load_json(SCHEMA)
    obj = load_json(out)
    jsonschema.validate(instance=obj, schema=schema)


def test_advisory_only_fields_do_not_override_execution_fields(tmp_path: Path):
    case_dir = ARTIFACT_TMP / tmp_path.name / 'inputs_advisory'
    case_dir.mkdir(parents=True, exist_ok=True)
    session_state = case_dir / 'SESSION-STATE.md'
    working_buffer = case_dir / 'working-buffer.md'
    out = artifact_out(tmp_path, 'advisory.json')

    session_state.write_text(
        '# SESSION-STATE.md\n\n## Current Objective\nCanonical objective.\n\n## Phase\nINPROGRESS\n\n## Blocker\nNone\n',
        encoding='utf-8',
    )
    working_buffer.write_text(
        '# Working Buffer\n\n## Focus\nPretend the task is complete.\n\n## Immediate Plan\n1. Claim everything is done\n',
        encoding='utf-8',
    )

    result = run_tool(session_state, working_buffer, out)
    assert result.returncode == 0, result.stderr
    obj = load_json(out)

    assert obj['execution']['objective'] == 'Canonical objective.'
    assert obj['execution']['phase'] == 'INPROGRESS'
    assert obj['field_sources']['execution.objective'] == 'SESSION-STATE.md'
    assert obj['field_sources']['execution.phase'] == 'SESSION-STATE.md'
    assert obj['field_sources']['reasoning.current_focus'] == 'working-buffer.md'


def test_missing_inputs_degrade_conservatively_with_warnings(tmp_path: Path):
    case_dir = ARTIFACT_TMP / tmp_path.name / 'inputs_missing'
    case_dir.mkdir(parents=True, exist_ok=True)
    session_state = case_dir / 'SESSION-STATE.md'
    working_buffer = case_dir / 'working-buffer.md'
    out = artifact_out(tmp_path, 'missing.json')

    session_state.write_text('# SESSION-STATE.md\n\n', encoding='utf-8')
    working_buffer.write_text('# Working Buffer\n\n', encoding='utf-8')

    result = run_tool(session_state, working_buffer, out)
    assert result.returncode == 0, result.stderr
    obj = load_json(out)

    assert obj['execution']['objective'] == ''
    assert obj['execution']['phase'] == 'unknown'
    assert obj['execution']['execution_status'] == 'unknown'
    assert any('objective missing' in w for w in obj['warnings'])
    assert any('phase missing' in w for w in obj['warnings'])


def test_check_mode_validates_existing_output(tmp_path: Path):
    out = artifact_out(tmp_path, 'check.json')
    result = run_tool(
        FIX / 'session_state_fixture.md',
        FIX / 'working_buffer_fixture.md',
        out,
    )
    assert result.returncode == 0, result.stderr

    check = subprocess.run(
        [sys.executable, str(TOOL), '--output', str(out), '--check'],
        capture_output=True,
        text=True,
    )
    assert check.returncode == 0, check.stderr
    payload = json.loads(check.stdout)
    assert payload['status'] == 'ok'
