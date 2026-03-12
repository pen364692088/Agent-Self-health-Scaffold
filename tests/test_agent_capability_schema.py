import json
from pathlib import Path

W = Path(__file__).resolve().parent.parent

def test_capability_schema_is_valid():
    schema_path = W / 'schemas' / 'AGENT_CAPABILITY.schema.json'
    assert schema_path.exists()
    schema = json.loads(schema_path.read_text())
    assert schema['title'] == 'Agent Capability Contract'
    assert 'capability_id' in schema['required']
    assert 'category' in schema['required']

def test_proposal_schema_is_valid():
    schema_path = W / 'schemas' / 'AGENT_PROPOSAL.schema.json'
    assert schema_path.exists()
    schema = json.loads(schema_path.read_text())
    assert schema['title'] == 'Agent Proposal Contract'
    assert 'proposal_id' in schema['required']
    assert 'shadow_plan' in schema['required']

def test_capability_contract_policy_exists():
    policy_path = W / 'POLICIES' / 'AGENT_CAPABILITY_CONTRACT.md'
    assert policy_path.exists()
    content = policy_path.read_text()
    assert 'user_promised_feature' in content

def test_proposal_policy_exists():
    policy_path = W / 'POLICIES' / 'AGENT_PROPOSAL_POLICY.md'
    assert policy_path.exists()
    content = policy_path.read_text()
    assert 'proposal_only' in content.lower() or 'proposal-only' in content.lower()
