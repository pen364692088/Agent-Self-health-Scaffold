#!/usr/bin/env python3
"""
Memory Template Generator

为 Agent 生成私有记忆空间模板。

Author: Agent-Self-health-Scaffold
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import yaml
from typing import Optional, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class MemoryTemplateGenerator:
    """
    私有记忆空间模板生成器
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.memory_root = project_root / "memory" / "agents"
        self.baseline_root = project_root / "memory" / "baseline"
    
    def generate_instruction_rules(
        self,
        agent_id: str,
        role: str,
        workflow_rules: Optional[list] = None,
        mutation_allowed_paths: Optional[list] = None,
        mutation_forbidden_paths: Optional[list] = None,
    ) -> str:
        """
        生成 instruction_rules.yaml
        
        Args:
            agent_id: Agent ID
            role: Agent 角色
            workflow_rules: 自定义工作流规则
            mutation_allowed_paths: 允许变更的路径
            mutation_forbidden_paths: 禁止变更的路径
        
        Returns:
            YAML 内容
        """
        content = f"""# Agent-Specific Instruction Rules Overlay
# 继承全局 baseline，agent-specific 规则作为 overlay

version: "1.0"
agent_id: {agent_id}
base: global  # 继承全局 baseline

# Agent-specific workflow rules (override global)
workflow_rules:
"""
        
        # 默认工作流规则
        if workflow_rules is None:
            workflow_rules = self._get_default_workflow_rules(role)
        
        for rule in workflow_rules:
            content += f"""  - id: {rule['id']}
    description: "{rule['description']}"
    priority: {rule.get('priority', 10)}
"""
        
        # 变更约束
        content += """
# Agent-specific mutation rules (merged with global)
mutation_rules:
"""
        
        if mutation_allowed_paths:
            content += "  allowed_paths:\n"
            for path in mutation_allowed_paths:
                content += f"    - \"{path}\"\n"
        else:
            content += "  allowed_paths: []\n"
        
        if mutation_forbidden_paths:
            content += "  forbidden_paths:\n"
            for path in mutation_forbidden_paths:
                content += f"    - \"{path}\"\n"
        else:
            content += "  forbidden_paths: []\n"
        
        return content
    
    def _get_default_workflow_rules(self, role: str) -> list:
        """获取角色默认工作流规则"""
        role_rules = {
            "planner": [
                {"id": "read-status-first", "description": "每次启动时必须先读取 STATUS.md 和 TODO.md", "priority": 1},
                {"id": "check-constraints", "description": "规划前必须检查约束条件", "priority": 2},
                {"id": "atomic-tasks", "description": "任务必须是原子化的、可测试的", "priority": 3},
            ],
            "implementer": [
                {"id": "read-design-before-impl", "description": "实现前必须阅读设计文档", "priority": 1},
                {"id": "write-tests-alongside", "description": "编写代码时必须同时编写测试", "priority": 2},
                {"id": "run-smoke-before-commit", "description": "提交前必须运行 smoke 测试", "priority": 3},
            ],
            "verifier": [
                {"id": "read-acceptance-first", "description": "测试前必须先读取完成标准", "priority": 1},
                {"id": "smoke-then-fast-then-full", "description": "按顺序执行：smoke → fast → full", "priority": 2},
                {"id": "document-all-results", "description": "必须记录所有测试结果", "priority": 3},
            ],
            "merger": [
                {"id": "verify-all-tests-pass", "description": "合并前必须验证所有测试通过", "priority": 1},
                {"id": "resolve-conflicts-carefully", "description": "必须仔细解决冲突", "priority": 2},
            ],
            "scribe": [
                {"id": "record-all-decisions", "description": "必须记录所有决策", "priority": 1},
                {"id": "update-status-on-change", "description": "状态变化时必须更新 STATUS.md", "priority": 2},
            ],
            "coordinator": [
                {"id": "check-agent-availability", "description": "分配任务前必须检查 Agent 可用性", "priority": 1},
                {"id": "track-progress", "description": "必须追踪进度并汇报", "priority": 2},
            ],
        }
        
        return role_rules.get(role, [])
    
    def generate_handoff_state(self, agent_id: str) -> str:
        """生成 handoff_state.yaml"""
        return f"""agent_id: {agent_id}
objective: 等待任务分配
phase: idle
next_actions: []
blockers: []
timestamp: {datetime.now(timezone.utc).isoformat()}
"""
    
    def generate_execution_state(self, agent_id: str) -> str:
        """生成 execution_state.yaml"""
        return f"""agent_id: {agent_id}
status: idle
task_id: null
step: null
timestamp: {datetime.now(timezone.utc).isoformat()}
"""
    
    def create_memory_space(
        self,
        agent_id: str,
        role: str,
        workflow_rules: Optional[list] = None,
        mutation_allowed_paths: Optional[list] = None,
        mutation_forbidden_paths: Optional[list] = None,
    ) -> Path:
        """
        创建完整的私有记忆空间
        
        Args:
            agent_id: Agent ID
            role: Agent 角色
            workflow_rules: 自定义工作流规则
            mutation_allowed_paths: 允许变更的路径
            mutation_forbidden_paths: 禁止变更的路径
        
        Returns:
            记忆空间根路径
        """
        # 创建目录
        memory_dir = self.memory_root / agent_id
        long_term_dir = memory_dir / "long_term"
        
        memory_dir.mkdir(parents=True, exist_ok=True)
        long_term_dir.mkdir(exist_ok=True)
        
        # 生成 instruction_rules.yaml
        instruction_rules = self.generate_instruction_rules(
            agent_id=agent_id,
            role=role,
            workflow_rules=workflow_rules,
            mutation_allowed_paths=mutation_allowed_paths,
            mutation_forbidden_paths=mutation_forbidden_paths,
        )
        
        with open(memory_dir / "instruction_rules.yaml", "w") as f:
            f.write(instruction_rules)
        
        # 生成 handoff_state.yaml
        with open(memory_dir / "handoff_state.yaml", "w") as f:
            f.write(self.generate_handoff_state(agent_id))
        
        # 生成 execution_state.yaml
        with open(memory_dir / "execution_state.yaml", "w") as f:
            f.write(self.generate_execution_state(agent_id))
        
        return memory_dir


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Memory Template")
    parser.add_argument("--agent-id", required=True, help="Agent ID")
    parser.add_argument("--role", required=True, help="Agent role")
    parser.add_argument("--dry-run", action="store_true", help="Print templates without creating")
    
    args = parser.parse_args()
    
    generator = MemoryTemplateGenerator(PROJECT_ROOT)
    
    if args.dry_run:
        print("=== instruction_rules.yaml ===")
        print(generator.generate_instruction_rules(args.agent_id, args.role))
        print("\n=== handoff_state.yaml ===")
        print(generator.generate_handoff_state(args.agent_id))
        print("\n=== execution_state.yaml ===")
        print(generator.generate_execution_state(args.agent_id))
    else:
        path = generator.create_memory_space(
            agent_id=args.agent_id,
            role=args.role,
        )
        print(f"✅ Memory space created at: {path}")


if __name__ == "__main__":
    main()
