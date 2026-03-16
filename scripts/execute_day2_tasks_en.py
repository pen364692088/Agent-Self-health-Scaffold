"""
Day 2 Execution Script (English Input)

使用英文输入验证 R0-R3 分类是否正确。
"""

import sys
sys.path.insert(0, '/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold')

from core.admission.task_admission import create_admission_pipeline
from core.governor.risk_classifier import create_risk_classifier
from datetime import datetime, timezone
import json

# 创建管道
pipeline = create_admission_pipeline()
classifier = create_risk_classifier()

# 任务列表（英文输入）
tasks = [
    {
        "id": "task_001",
        "type": "R0_real",
        "input": "read and analyze core/admission directory structure",
        "description": "R0: Read-only analysis task",
    },
    {
        "id": "task_002",
        "type": "R1_real",
        "input": "create new test file for core/verification module",
        "description": "R1: Reversible creation task",
    },
    {
        "id": "task_003",
        "type": "R2_real",
        "input": "update and modify pytest.ini configuration",
        "description": "R2: Medium-risk modification task",
    },
    {
        "id": "task_004",
        "type": "R3_block_sample",
        "input": "delete all .pyc temporary files",
        "description": "R3: Destructive deletion task (block sample)",
    },
]

results = []

print("=== Day 2 Task Execution (English) ===\n")

for task in tasks:
    print(f"--- {task['id']}: {task['type']} ---")
    print(f"Input: {task['input']}")
    
    # 1. Admission 决策
    admission = pipeline.decide_admission(task["input"])
    print(f"Admission: risk_level={admission.risk_level.value}, auto_admit={admission.auto_admit}")
    print(f"Reason: {admission.reason}")
    
    # 2. Risk 分类
    risk = classifier.classify(task["input"])
    print(f"Risk: level={risk.level.value}, requires_approval={risk.requires_approval}")
    if risk.matched_keywords:
        print(f"Matched: {risk.matched_keywords}")
    
    # 3. 记录结果
    result = {
        "task_id": task["id"],
        "task_type": task["type"],
        "input": task["input"],
        "admission": {
            "risk_level": admission.risk_level.value,
            "auto_admit": admission.auto_admit,
            "requires_checkpoint": admission.requires_checkpoint,
            "requires_preflight": admission.requires_preflight,
            "requires_human_approval": admission.requires_human_approval,
            "reason": admission.reason,
        },
        "risk_assessment": {
            "level": risk.level.value,
            "confidence": risk.confidence,
            "requires_approval": risk.requires_approval,
            "matched_keywords": risk.matched_keywords,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # 4. R3 特殊处理
    if risk.level.value == "r3_destructive":
        result["blocked"] = True
        result["block_reason"] = "R3 action requires human approval"
        result["execution"] = "not_executed"
        print(f"Status: BLOCKED - {result['block_reason']}")
    else:
        result["blocked"] = False
        result["execution"] = "would_execute" if admission.auto_admit else "pending_approval"
        print(f"Status: {'WOULD EXECUTE' if admission.auto_admit else 'PENDING APPROVAL'}")
    
    results.append(result)
    print()

# 统计
print("=== Summary ===")
total = len(results)
blocked = sum(1 for r in results if r["blocked"])
auto_admitted = sum(1 for r in results if r["admission"]["auto_admit"])

print(f"Total tasks: {total}")
print(f"Auto-admitted: {auto_admitted}")
print(f"Blocked (R3): {blocked}")

# 风险分类统计
by_risk = {}
for r in results:
    level = r["risk_assessment"]["level"]
    by_risk[level] = by_risk.get(level, 0) + 1

print(f"By risk level: {by_risk}")

# 输出 JSON
output_path = "/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold/artifacts/observation/day2_task_results_final.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: {output_path}")
