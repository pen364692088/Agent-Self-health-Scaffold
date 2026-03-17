#!/usr/bin/env python3
"""
Agent Profile Generator

标准化生成 Agent Profile。

Author: Agent-Self-health-Scaffold
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import json
from typing import Optional, List, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class AgentProfileGenerator:
    """
    Agent Profile 生成器
    
    提供标准化的 Agent Profile 生成能力。
    """
    
    # 支持的角色类型
    ROLES = ["planner", "implementer", "verifier", "merger", "scribe", "coordinator", "specialist"]
    
    # 角色默认模板
    ROLE_TEMPLATES = {
        "planner": {
            "description": "规划 Agent，负责分解复杂任务并制定可执行计划",
            "capabilities": [
                {"name": "task_decomposition", "level": "expert"},
                {"name": "dependency_analysis", "level": "advanced"},
                {"name": "acceptance_criteria", "level": "expert"},
            ],
            "inputs": ["requirements", "existing_status", "historical_context"],
            "outputs": ["task_breakdown", "acceptance_criteria", "risk_assessment"],
            "mutation_paths": ["docs/TODO.md", "docs/STATUS.md", "docs/DECISIONS.md"],
        },
        "implementer": {
            "description": "实现 Agent，负责执行任务并产出工作代码",
            "capabilities": [
                {"name": "code_implementation", "level": "expert"},
                {"name": "test_writing", "level": "advanced"},
                {"name": "git_operations", "level": "advanced"},
            ],
            "inputs": ["task_from_TODO", "design_from_planner", "existing_codebase"],
            "outputs": ["working_code", "tests", "git_commits", "status_updates"],
            "mutation_paths": ["src/", "tests/", "docs/STATUS.md", "docs/TODO.md"],
        },
        "verifier": {
            "description": "验证 Agent，负责测试审计和质量保证",
            "capabilities": [
                {"name": "test_execution", "level": "expert"},
                {"name": "acceptance_verification", "level": "expert"},
                {"name": "regression_detection", "level": "advanced"},
            ],
            "inputs": ["code_from_implementer", "acceptance_criteria", "test_suite"],
            "outputs": ["test_results", "audit_findings", "pass_fail_determination"],
            "mutation_paths": ["reports/", "docs/STATUS.md"],
        },
        "merger": {
            "description": "合并 Agent，负责集成多个 Agent 的工作",
            "capabilities": [
                {"name": "branch_management", "level": "expert"},
                {"name": "conflict_resolution", "level": "advanced"},
                {"name": "release_management", "level": "advanced"},
            ],
            "inputs": ["completed_work", "test_results", "feature_branches"],
            "outputs": ["merged_code", "release_notes", "completion_report"],
            "mutation_paths": ["docs/CHANGELOG.md", "docs/STATUS.md"],
        },
        "scribe": {
            "description": "记录 Agent，负责文档和决策记录",
            "capabilities": [
                {"name": "documentation", "level": "expert"},
                {"name": "decision_recording", "level": "expert"},
                {"name": "handoff_preparation", "level": "advanced"},
            ],
            "inputs": ["work_from_others", "decisions", "session_notes"],
            "outputs": ["updated_docs", "handoff_notes", "session_summaries"],
            "mutation_paths": ["docs/", "memory/"],
        },
        "coordinator": {
            "description": "协调 Agent，负责多 Agent 协作编排",
            "capabilities": [
                {"name": "task_routing", "level": "expert"},
                {"name": "agent_coordination", "level": "expert"},
                {"name": "progress_tracking", "level": "advanced"},
            ],
            "inputs": ["tasks", "agent_status", "resource_availability"],
            "outputs": ["task_assignments", "progress_reports", "escalations"],
            "mutation_paths": ["docs/STATUS.md", "docs/TODO.md"],
        },
        "specialist": {
            "description": "专家 Agent，负责特定领域任务",
            "capabilities": [
                {"name": "domain_expertise", "level": "expert"},
            ],
            "inputs": ["specialized_task"],
            "outputs": ["specialized_output"],
            "mutation_paths": [],
        },
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.agents_dir = project_root / "agents"
        self.agents_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(
        self,
        agent_id: str,
        name: str,
        role: str,
        description: Optional[str] = None,
        capabilities: Optional[List[Dict[str, str]]] = None,
        pilot: bool = False,
        custom_mutation_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        生成 Agent Profile
        
        Args:
            agent_id: Agent 唯一标识
            name: Agent 显示名称
            role: 角色类型
            description: 描述（可选，使用模板默认值）
            capabilities: 能力列表（可选，使用模板默认值）
            pilot: 是否为 pilot agent
            custom_mutation_paths: 自定义变更路径（可选）
        
        Returns:
            Agent Profile 字典
        """
        # 验证 role
        if role not in self.ROLES:
            raise ValueError(f"Invalid role: {role}. Must be one of {self.ROLES}")
        
        # 获取模板
        template = self.ROLE_TEMPLATES.get(role, {})
        
        # 构建能力列表
        if capabilities is None:
            capabilities = template.get("capabilities", [])
        
        # 构建变更路径
        if custom_mutation_paths is None:
            mutation_paths = template.get("mutation_paths", [])
        else:
            mutation_paths = custom_mutation_paths
        
        # 构建 profile
        profile = {
            "agent_id": agent_id,
            "name": name,
            "role": role,
            "description": description or template.get("description", ""),
            "capabilities": capabilities,
            "memory_config": {
                "memory_root": f"memory/agents/{agent_id}",
                "instruction_rules_file": "instruction_rules.yaml",
                "handoff_file": "handoff_state.yaml",
                "execution_state_file": "execution_state.yaml",
                "long_term_memory_dir": "long_term",
            },
            "runtime_config": {
                "max_retries": 3,
                "timeout_seconds": 300,
                "enable_mutation_guard": True,
                "enable_canonical_guard": True,
                "allowed_mutation_paths": mutation_paths,
            },
            "inputs": template.get("inputs", []),
            "outputs": template.get("outputs", []),
            "working_rules": {
                "must_do": [],
                "must_not_do": [],
            },
            "status": "inactive",
            "pilot": pilot,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        return profile
    
    def save(self, profile: Dict[str, Any]) -> Path:
        """
        保存 Agent Profile 到文件
        
        Args:
            profile: Agent Profile 字典
        
        Returns:
            保存的文件路径
        """
        agent_id = profile["agent_id"]
        profile_path = self.agents_dir / f"{agent_id}.profile.json"
        
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        return profile_path
    
    def generate_and_save(
        self,
        agent_id: str,
        name: str,
        role: str,
        **kwargs,
    ) -> Path:
        """
        生成并保存 Agent Profile
        
        Returns:
            保存的文件路径
        """
        profile = self.generate(agent_id, name, role, **kwargs)
        return self.save(profile)


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Agent Profile")
    parser.add_argument("--agent-id", required=True, help="Agent ID")
    parser.add_argument("--name", required=True, help="Agent display name")
    parser.add_argument("--role", required=True, choices=AgentProfileGenerator.ROLES, help="Agent role")
    parser.add_argument("--description", help="Agent description")
    parser.add_argument("--pilot", action="store_true", help="Mark as pilot agent")
    parser.add_argument("--dry-run", action="store_true", help="Print profile without saving")
    
    args = parser.parse_args()
    
    generator = AgentProfileGenerator(PROJECT_ROOT)
    
    if args.dry_run:
        profile = generator.generate(
            agent_id=args.agent_id,
            name=args.name,
            role=args.role,
            description=args.description,
            pilot=args.pilot,
        )
        print(json.dumps(profile, indent=2, ensure_ascii=False))
    else:
        path = generator.generate_and_save(
            agent_id=args.agent_id,
            name=args.name,
            role=args.role,
            description=args.description,
            pilot=args.pilot,
        )
        print(f"✅ Agent profile saved to: {path}")


if __name__ == "__main__":
    main()
