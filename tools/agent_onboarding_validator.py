#!/usr/bin/env python3
"""
Agent Onboarding Validator

新 Agent 接入验证流水线：
1. Schema 校验
2. Memory 完整性检查
3. 冷启动样本
4. 最小 E2E
5. 隔离性检查

Author: Agent-Self-health-Scaffold
Created: 2026-03-17
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import json
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class OnboardingValidator:
    """
    新 Agent 接入验证器
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.agents_dir = project_root / "agents"
        self.memory_dir = project_root / "memory" / "agents"
        self.schema_dir = project_root / "schemas"
    
    def validate_all(self, agent_id: str) -> Dict[str, Any]:
        """
        执行完整验证流水线
        
        Args:
            agent_id: Agent ID
        
        Returns:
            验证结果
        """
        results = {
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "passed": True,
            "errors": [],
        }
        
        print(f"\n{'='*60}")
        print(f"AGENT ONBOARDING VALIDATION: {agent_id}")
        print(f"{'='*60}\n")
        
        # 1. Schema 校验
        results["checks"]["schema"] = self._validate_schema(agent_id)
        
        # 2. Memory 完整性检查
        results["checks"]["memory_integrity"] = self._validate_memory_integrity(agent_id)
        
        # 3. 冷启动样本
        results["checks"]["cold_start"] = self._validate_cold_start(agent_id)
        
        # 4. 最小 E2E
        results["checks"]["e2e"] = self._validate_e2e(agent_id)
        
        # 5. 隔离性检查
        results["checks"]["isolation"] = self._validate_isolation(agent_id)
        
        # 汇总结果
        for check_name, check_result in results["checks"].items():
            if not check_result.get("passed", False):
                results["passed"] = False
                results["errors"].append(f"{check_name}: {check_result.get('error', 'failed')}")
        
        return results
    
    def _validate_schema(self, agent_id: str) -> Dict[str, Any]:
        """验证 Agent Profile Schema"""
        print("📋 CHECK 1: Schema Validation")
        
        result = {"passed": False, "details": []}
        
        try:
            # 加载 profile
            profile_path = self.agents_dir / f"{agent_id}.profile.json"
            if not profile_path.exists():
                result["error"] = "Profile file not found"
                print(f"  ❌ Profile file not found: {profile_path}")
                return result
            
            with open(profile_path, "r") as f:
                profile = json.load(f)
            
            # 加载 schema
            schema_path = self.schema_dir / "agent_profile.v1.schema.json"
            if not schema_path.exists():
                result["error"] = "Schema file not found"
                print(f"  ❌ Schema file not found: {schema_path}")
                return result
            
            with open(schema_path, "r") as f:
                schema = json.load(f)
            
            # 验证必需字段
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in profile:
                    result["error"] = f"Missing required field: {field}"
                    print(f"  ❌ Missing required field: {field}")
                    return result
                result["details"].append(f"✅ {field}: present")
                print(f"  ✅ {field}: present")
            
            # 验证 agent_id 格式
            import re
            if not re.match(r"^[a-z][a-z0-9_-]*$", profile.get("agent_id", "")):
                result["error"] = "Invalid agent_id format"
                print(f"  ❌ Invalid agent_id format")
                return result
            
            print(f"  ✅ agent_id format valid")
            
            # 验证 role
            valid_roles = ["planner", "implementer", "verifier", "merger", "scribe", "coordinator", "specialist"]
            if profile.get("role") not in valid_roles:
                result["error"] = f"Invalid role: {profile.get('role')}"
                print(f"  ❌ Invalid role: {profile.get('role')}")
                return result
            
            print(f"  ✅ role valid: {profile.get('role')}")
            
            result["passed"] = True
            print("  ✅ Schema validation passed")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ Error: {e}")
        
        return result
    
    def _validate_memory_integrity(self, agent_id: str) -> Dict[str, Any]:
        """验证 Memory 完整性"""
        print("\n📋 CHECK 2: Memory Integrity")
        
        result = {"passed": False, "details": []}
        
        try:
            memory_root = self.memory_dir / agent_id
            
            # 检查必需文件
            required_files = [
                "instruction_rules.yaml",
                "handoff_state.yaml",
                "execution_state.yaml",
            ]
            
            for file_name in required_files:
                file_path = memory_root / file_name
                if not file_path.exists():
                    result["error"] = f"Missing file: {file_name}"
                    print(f"  ❌ Missing file: {file_name}")
                    return result
                print(f"  ✅ {file_name}: exists")
            
            # 检查 long_term 目录
            long_term_dir = memory_root / "long_term"
            if not long_term_dir.exists():
                result["error"] = "Missing long_term directory"
                print(f"  ❌ Missing long_term directory")
                return result
            
            print(f"  ✅ long_term/: exists")
            
            # 验证 instruction_rules 内容
            import yaml
            with open(memory_root / "instruction_rules.yaml", "r") as f:
                rules = yaml.safe_load(f)
            
            if rules.get("agent_id") != agent_id:
                result["error"] = "instruction_rules agent_id mismatch"
                print(f"  ❌ instruction_rules agent_id mismatch")
                return result
            
            print(f"  ✅ instruction_rules: agent_id matches")
            
            if rules.get("base") != "global":
                result["error"] = "instruction_rules must declare base: global"
                print(f"  ❌ instruction_rules must declare base: global")
                return result
            
            print(f"  ✅ instruction_rules: base=global")
            
            result["passed"] = True
            print("  ✅ Memory integrity check passed")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ Error: {e}")
        
        return result
    
    def _validate_cold_start(self, agent_id: str) -> Dict[str, Any]:
        """验证冷启动样本"""
        print("\n📋 CHECK 3: Cold Start Sample")
        
        result = {"passed": False, "details": []}
        
        try:
            from core.agent_profile import AgentProfileRegistry
            from memory_runtime.session_bootstrap import SessionBootstrap, BootstrapConfig
            
            # 加载 profile
            registry = AgentProfileRegistry(self.project_root)
            registry.load_all()
            
            profile = registry.get(agent_id)
            if not profile:
                result["error"] = "Profile not found in registry"
                print(f"  ❌ Profile not found in registry")
                return result
            
            print(f"  ✅ Profile loaded from registry")
            
            # 创建记忆空间
            memory_root = registry.create_memory_space(agent_id)
            print(f"  ✅ Memory space: {memory_root}")
            
            # 执行 bootstrap
            config = BootstrapConfig(
                agent_id=agent_id,
                memory_root=memory_root,
            )
            
            bootstrap = SessionBootstrap(config)
            bootstrap_result = bootstrap.run()
            
            if not bootstrap_result.success:
                result["error"] = "Bootstrap failed"
                print(f"  ❌ Bootstrap failed")
                return result
            
            print(f"  ✅ Bootstrap succeeded")
            print(f"  ✅ Rules loaded: {bootstrap_result.instruction_rules.get('rule_count', 0)}")
            
            # 状态写回
            from memory_runtime.execution_state_manager import ExecutionStateManager
            
            state_manager = ExecutionStateManager(
                agent_id=agent_id,
                memory_root=memory_root,
            )
            
            state_manager.save(status="ready", step="cold_start_test")
            loaded = state_manager.load()
            
            if loaded.get("status") != "ready":
                result["error"] = "State writeback failed"
                print(f"  ❌ State writeback failed")
                return result
            
            print(f"  ✅ State writeback verified")
            
            result["passed"] = True
            print("  ✅ Cold start sample passed")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def _validate_e2e(self, agent_id: str) -> Dict[str, Any]:
        """验证最小 E2E"""
        print("\n📋 CHECK 4: Minimal E2E")
        
        result = {"passed": False, "details": []}
        
        try:
            from core.agent_profile import AgentProfileRegistry
            from execution_runtime.preflight import PreflightChecker, PreflightConfig, PreflightCheck
            from execution_runtime.mutation_guard import MutationGuard, MutationConfig, MutationType
            
            # 加载 profile
            registry = AgentProfileRegistry(self.project_root)
            registry.load_all()
            
            profile = registry.get(agent_id)
            memory_root = registry.create_memory_space(agent_id)
            
            # Preflight 检查
            preflight_config = PreflightConfig(
                agent_id=agent_id,
                checks=[PreflightCheck.MEMORY, PreflightCheck.REPO_ROOT, PreflightCheck.STATE],
                canonical_repo=self.project_root,
            )
            
            checker = PreflightChecker(preflight_config)
            preflight_result = checker.check_all()
            
            print(f"  ✅ Preflight completed")
            
            # Mutation Guard 检查
            guard_config = MutationConfig(
                agent_id=agent_id,
                allow_create=True,
                allow_update=True,
                allow_delete=False,
                protected_paths=[self.project_root / ".git"],
            )
            
            guard = MutationGuard(guard_config)
            
            # 测试禁止路径
            test_result = guard.check(MutationType.UPDATE, Path(".git/config"))
            if test_result.decision.value != "block":
                result["error"] = "Mutation guard failed to block .git"
                print(f"  ❌ Mutation guard failed to block .git")
                return result
            
            print(f"  ✅ Mutation guard blocks .git")
            
            result["passed"] = True
            print("  ✅ Minimal E2E passed")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def _validate_isolation(self, agent_id: str) -> Dict[str, Any]:
        """验证隔离性"""
        print("\n📋 CHECK 5: Isolation Check")
        
        result = {"passed": False, "details": []}
        
        try:
            # 检查记忆空间隔离
            memory_root = self.memory_dir / agent_id
            
            # 检查是否与其他 Agent 的记忆空间独立
            other_agents = []
            for agent_dir in self.memory_dir.iterdir():
                if agent_dir.is_dir() and agent_dir.name != agent_id:
                    other_agents.append(agent_dir.name)
            
            print(f"  ✅ Other agents: {other_agents}")
            
            # 验证没有文件交叉
            agent_files = set()
            for f in memory_root.rglob("*"):
                if f.is_file():
                    agent_files.add(str(f.relative_to(self.memory_dir)))
            
            for other_agent in other_agents:
                other_root = self.memory_dir / other_agent
                other_files = set()
                for f in other_root.rglob("*"):
                    if f.is_file():
                        other_files.add(str(f.relative_to(self.memory_dir)))
                
                overlap = agent_files & other_files
                if overlap:
                    result["error"] = f"File overlap with {other_agent}: {overlap}"
                    print(f"  ❌ File overlap with {other_agent}")
                    return result
            
            print(f"  ✅ No file overlap with other agents")
            
            # 验证状态隔离
            import yaml
            with open(memory_root / "execution_state.yaml", "r") as f:
                state = yaml.safe_load(f)
            
            if state.get("agent_id") != agent_id:
                result["error"] = "execution_state agent_id mismatch"
                print(f"  ❌ execution_state agent_id mismatch")
                return result
            
            print(f"  ✅ execution_state agent_id matches")
            
            result["passed"] = True
            print("  ✅ Isolation check passed")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ Error: {e}")
        
        return result


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Agent Onboarding")
    parser.add_argument("--agent-id", required=True, help="Agent ID to validate")
    
    args = parser.parse_args()
    
    validator = OnboardingValidator(PROJECT_ROOT)
    results = validator.validate_all(args.agent_id)
    
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    for check_name, check_result in results["checks"].items():
        status = "✅ PASS" if check_result.get("passed") else "❌ FAIL"
        print(f"{check_name}: {status}")
    
    if results["passed"]:
        print(f"\n✅ ALL CHECKS PASSED - Agent {args.agent_id} is ready for onboarding")
        sys.exit(0)
    else:
        print(f"\n❌ VALIDATION FAILED")
        for error in results["errors"]:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
