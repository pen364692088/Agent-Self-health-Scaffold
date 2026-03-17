import json
from pathlib import Path
from datetime import datetime

# 创建 B1-2 任务：验证和补全 Identity Invariants 系统

task_id = "pilot_b12_identity_verify"
task_dir = Path("artifacts/tasks") / task_id
task_dir.mkdir(parents=True, exist_ok=True)

output_dir = task_dir / "output"
output_dir.mkdir(parents=True, exist_ok=True)
(task_dir / "steps").mkdir(exist_ok=True)
(task_dir / "evidence").mkdir(exist_ok=True)

# S04 的 Python 脚本
s04_script = '''
import json
from pathlib import Path

schema_path = Path('contracts/identity_invariants.schema.json')
with open(schema_path) as f:
    schema = json.load(f)

print(f'Schema loaded: {len(schema.get("properties", {}))} properties')
print(f'Required fields: {len(schema.get("required", []))}')

from egocore.runtime.identity_guard import IdentityGuard
guard = IdentityGuard()
print(f'IdentityGuard initialized')

result = guard.validate_change('core_name', 'Test Name')
print(f'Validate core_name change: {result}')
'''

# 写入脚本文件
script_file = task_dir / "s04_test_guard.py"
with open(script_file, 'w') as f:
    f.write(s04_script)

# 具体的验证任务
task_state = {
    "task_id": task_id,
    "task_name": "B1-2 Identity Invariants 验证",
    "description": "验证 EgoCore identity_invariants 系统完整性，测试 guard 功能",
    "status": "created",
    "created_at": datetime.utcnow().isoformat() + "Z",
    "updated_at": datetime.utcnow().isoformat() + "Z",
    "steps": {
        "S01": {
            "step_id": "S01",
            "step_name": "验证 schema 文件存在",
            "status": "pending",
            "depends_on": [],
            "step_type": "execute_shell",
            "command": "test -f /home/moonlight/Project/Github/MyProject/EgoCore/contracts/identity_invariants.schema.json && echo 'Schema exists' > artifacts/tasks/pilot_b12_identity_verify/output/s01_schema_check.txt"
        },
        "S02": {
            "step_id": "S02",
            "step_name": "验证 identity_guard.py 存在",
            "status": "pending",
            "depends_on": ["S01"],
            "step_type": "execute_shell",
            "command": "test -f /home/moonlight/Project/Github/MyProject/EgoCore/egocore/runtime/identity_guard.py && echo 'Guard exists' > artifacts/tasks/pilot_b12_identity_verify/output/s02_guard_check.txt"
        },
        "S03": {
            "step_id": "S03",
            "step_name": "导入测试 identity_guard",
            "status": "pending",
            "depends_on": ["S02"],
            "step_type": "execute_shell",
            "command": "cd /home/moonlight/Project/Github/MyProject/EgoCore && python3 -c \"from egocore.runtime.identity_guard import IdentityGuard; print('Import OK')\" > /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold/artifacts/tasks/pilot_b12_identity_verify/output/s03_import_test.txt 2>&1"
        },
        "S04": {
            "step_id": "S04",
            "step_name": "测试 identity_guard 功能",
            "status": "pending",
            "depends_on": ["S03"],
            "step_type": "execute_shell",
            "command": "cd /home/moonlight/Project/Github/MyProject/EgoCore && python3 /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold/artifacts/tasks/pilot_b12_identity_verify/s04_test_guard.py > /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold/artifacts/tasks/pilot_b12_identity_verify/output/s04_guard_test.txt 2>&1"
        },
        "S05": {
            "step_id": "S05",
            "step_name": "生成验证报告",
            "status": "pending",
            "depends_on": ["S04"],
            "step_type": "execute_shell",
            "command": "echo '{\"task\": \"pilot_b12_identity_verify\", \"status\": \"completed\", \"verified_at\": \"'$(date -Iseconds)'\"}' > artifacts/tasks/pilot_b12_identity_verify/output/verification_report.json"
        }
    }
}

with open(task_dir / "task_state.json", 'w') as f:
    json.dump(task_state, f, indent=2)

print(f"✅ B1-2 任务创建: {task_id}")
print(f"   5 个验证步骤")
print(f"   目标: EgoCore identity_invariants 系统")
