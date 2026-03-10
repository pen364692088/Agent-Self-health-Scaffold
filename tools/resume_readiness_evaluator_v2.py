#!/usr/bin/env python3
"""
Resume-Readiness Evaluator V2

Gate-based scoring: Topic + Task Status required before any points.
No participation points - must demonstrate continuation capability.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")


def detect_topic(content: str) -> Tuple[bool, str]:
    """检测是否有明确主题"""
    # 强主题信号 - 项目/任务名称模式
    project_patterns = [
        # 明确的项目/任务命名
        r'[A-Z][a-zA-Z\s]+\s*(V\d+|v\d+)',  # "Context Compression V2"
        r'Gate\s*\d+\.?\d*',  # "Gate 1.5"
        r'Phase\s*\d+',  # "Phase 1"
        r'#\s*[^\n]{5,50}',  # Markdown 标题
        
        # 动词 + 名词结构
        r'(修复|实现|完成|构建|优化|验证|设计|重构|校准|部署)[^\n]{5,50}',
        
        # 名词 + 动词结构（中文）
        r'[^\n]*(验证|校准|测试|分析)[^\n]{0,30}$',
    ]
    
    for pattern in project_patterns:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return True, match.group(0)[:50].strip()
    
    # 中等信号 - 任务描述
    task_patterns = [
        r'(任务|目标|问题|工作)[：:]\s*[^\n]{5,}',
        r'(需要|应该|正在)[^\n]{5,}',
    ]
    
    for pattern in task_patterns:
        match = re.search(pattern, content)
        if match:
            return True, match.group(0)[:50].strip()
    
    # 弱信号 - 至少有实质性内容
    lines = [l.strip() for l in content.split('\n') if l.strip() and len(l.strip()) > 10]
    if len(lines) >= 3:
        # 检查是否有技术内容
        tech_indicators = ['.', '_', '/', 'api', 'config', 'script', 'tool']
        if any(ind in content.lower() for ind in tech_indicators):
            return True, "technical_content_detected"
    
    return False, ""


def is_task_completed(content: str) -> bool:
    """检测任务是否已完成"""
    completion_patterns = [
        r'✅\s*(完成|completed|done)',
        r'Task\s*(Completed|完成)',
        r'##\s*完成',
        r'已[经]?完成',
        r'全部完成',
        r'DONE\s*$',
    ]
    
    for pattern in completion_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    
    return False


def has_explicit_next_action(content: str) -> Tuple[bool, str]:
    """检测是否有明确的下一步"""
    patterns = [
        (r'(下一步|next)[：:]\s*([^\n]{5,})', 2),
        (r'(Phase \d+|阶段\s*\d+)[：:]\s*([^\n]{5,})', 0),
        (r'(待|需要|要)[做办写]?[：:]\s*([^\n]{5,})', 2),
        (r'(运行|执行|创建|编辑|修改|更新)\s*[^\n]{5,}', 0),
    ]
    
    for pattern, group in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            action = match.group(min(group, len(match.groups()))) if match.groups() else match.group(0)
            return True, action[:50]
    
    return False, ""


def has_decision_context(content: str) -> bool:
    """检测是否有决策上下文"""
    patterns = [
        r'(选择|决定|确认|采用|使用)[^\n]{5,}因为',
        r'(因为|由于|鉴于)[^\n]{5,}(选择|决定|确认)',
        r'(约束|限制|条件)[：:]',
        r'(不能|必须|不要|禁止)',
        r'(优先|重要|关键)',
    ]
    
    matches = sum(1 for p in patterns if re.search(p, content))
    return matches >= 2


def has_tool_state(content: str) -> Tuple[bool, List[str]]:
    """检测是否有工具/文件状态"""
    # 文件路径
    file_pattern = r'[a-zA-Z0-9_\-/]+\.(py|js|ts|json|md|sh|yaml|yml)'
    files = re.findall(file_pattern, content)
    
    # 工具名
    tool_pattern = r'(tools?|scripts?)/[a-zA-Z0-9_\-]+'
    tools = re.findall(tool_pattern, content)
    
    # 状态词
    status_pattern = r'(已创建|已修改|已删除|已更新|正在|pending)'
    has_status = bool(re.search(status_pattern, content))
    
    return bool(files or tools), files[:5]


def has_open_loops(content: str) -> Tuple[bool, List[str]]:
    """检测是否有未完成事项"""
    patterns = [
        r'(TODO|TBD|FIXME|XXX)[：:]?\s*([^\n]{5,})',
        r'(待[办做写确认]|尚未|还需要)[^\n]{5,}',
        r'(blocker|阻塞|问题)[：:]?\s*([^\n]{5,})',
    ]
    
    loops = []
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                loops.append(match[-1][:50] if match else "")
            else:
                loops.append(match[:50])
    
    return bool(loops), loops[:5]


def has_stale_constraint(content: str) -> bool:
    """检测是否有过期约束"""
    # 如果提到"之前"、"旧"、"不再"等，可能有过期信息
    stale_patterns = [
        r'之前\s*(决定|选择|方案)',
        r'旧的?',
        r'不再\s*(使用|需要|适用)',
        r'已(经)?\s*(废弃|移除|过时)',
    ]
    
    return any(re.search(p, content) for p in stale_patterns)


def compute_readiness_v2(content: str, events: List[Dict] = None) -> Dict:
    """
    计算 V2 readiness 分数
    
    Gate-based scoring:
    1. Gate 1: Topic present (mandatory)
    2. Gate 2: Task not completed (mandatory)
    3. Enhancement signals
    """
    result = {
        "readiness": 0.0,
        "gates": {},
        "signals": {},
        "penalties": {},
        "details": {}
    }
    
    # === Gate 1: Topic ===
    topic_ok, topic_text = detect_topic(content)
    result["gates"]["topic_present"] = topic_ok
    result["details"]["topic"] = topic_text
    
    if not topic_ok:
        result["readiness"] = 0.0
        result["gates"]["passed"] = False
        result["gates"]["failed_at"] = "topic"
        return result
    
    # === Gate 2: Task Status ===
    completed = is_task_completed(content)
    result["gates"]["task_active"] = not completed
    result["details"]["task_completed"] = completed
    
    if completed:
        result["readiness"] = 0.0
        result["gates"]["passed"] = False
        result["gates"]["failed_at"] = "task_completed"
        return result
    
    result["gates"]["passed"] = True
    
    # === Base Score ===
    score = 0.20  # Passed both gates
    
    # === Enhancement Signals ===
    
    # Signal A: Next Action
    next_ok, next_text = has_explicit_next_action(content)
    result["signals"]["next_action"] = next_ok
    result["details"]["next_action"] = next_text
    if next_ok:
        score += 0.30
    
    # Signal B: Decision Context
    context_ok = has_decision_context(content)
    result["signals"]["decision_context"] = context_ok
    if context_ok:
        score += 0.20
    
    # Signal C: Tool State
    tool_ok, tools = has_tool_state(content)
    result["signals"]["tool_state"] = tool_ok
    result["details"]["tools"] = tools
    if tool_ok:
        score += 0.15
    
    # Signal D: Open Loops
    loops_ok, loops = has_open_loops(content)
    result["signals"]["open_loops"] = loops_ok
    result["details"]["loops"] = loops
    if loops_ok:
        score += 0.15
    
    # === Penalties ===
    
    # Stale Constraint
    stale = has_stale_constraint(content)
    result["penalties"]["stale_constraint"] = stale
    if stale:
        score *= 0.5
    
    result["readiness"] = min(score, 1.0)
    
    return result


def evaluate_capsule(capsule_path: str) -> Dict:
    """评估单个 capsule"""
    with open(capsule_path) as f:
        data = json.load(f)
    
    content = data.get("content", "")
    if isinstance(content, list):
        content = "\n".join(content)
    
    events = data.get("events", [])
    
    return compute_readiness_v2(content, events)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Resume-Readiness Evaluator V2")
    parser.add_argument("--input", help="Path to capsule JSON")
    parser.add_argument("--content", help="Direct content string")
    parser.add_argument("--test", action="store_true", help="Run test cases")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    
    if args.test:
        test_cases = [
            # Test 1: High readiness
            {
                "content": """
# Gate 1.5 · Readiness Evaluator 校准

## Phase 1 进行中

下一步：标注 calibration error set

文件：tools/resume_readiness_calibration.py
约束：必须在 Gate 1.5 框架内修复
""",
                "expected": "high"
            },
            # Test 2: Zero - no topic
            {
                "content": "✅ New session started · model: qianfan-code-latest",
                "expected": "zero"
            },
            # Test 3: Zero - completed
            {
                "content": "✅ Task Completed: Monitoring Setup\n\nAll done!",
                "expected": "zero"
            },
            # Test 4: Moderate
            {
                "content": """
Context Compression V2 验证

正在运行测试...

文件已创建：
- tools/capsule-builder-v2.py
- schemas/session_capsule.v1.schema.json
""",
                "expected": "moderate"
            },
        ]
        
        results = []
        for i, test in enumerate(test_cases, 1):
            result = compute_readiness_v2(test["content"])
            results.append({
                "test": i,
                "expected": test["expected"],
                "actual_score": result["readiness"],
                "gates_passed": result["gates"]["passed"],
                "signals": result["signals"]
            })
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                print(f"Test {r['test']}: expected={r['expected']}, score={r['actual_score']:.2f}, gates={'✅' if r['gates_passed'] else '❌'}")
        
        return
    
    if args.content:
        result = compute_readiness_v2(args.content)
    elif args.input:
        result = evaluate_capsule(args.input)
    else:
        print("Use --content, --input, or --test")
        return
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Readiness: {result['readiness']:.2f}")
        print(f"Gates: {result['gates']}")
        print(f"Signals: {result['signals']}")
        if result.get('penalties'):
            print(f"Penalties: {result['penalties']}")


if __name__ == "__main__":
    main()
