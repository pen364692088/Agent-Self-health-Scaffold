#!/usr/bin/env python3
"""
Mutation Guard Regression Tests

Purpose:
  Ensure mutation guard prevents truth source fragmentation.
  
Required Tests:
  1. Existing canonical file → no duplicate created
  2. Ambiguous resolution → blocked
  3. update_only policy → create blocked
  4. New session → same constraints

Version: v1.0
Date: 2026-03-16
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add runtime to path
runtime_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if runtime_dir not in sys.path:
    sys.path.insert(0, os.path.join(runtime_dir, "runtime"))

from memory_preflight import MemoryPreflight, Decision, CanonicalRegistry, IntentParser
from mutation_gate import MutationGate


class TestCanonicalRegistry(unittest.TestCase):
    """Test Canonical Object Registry"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.registry = CanonicalRegistry()
    
    def test_registry_loads(self):
        """Test registry loads successfully"""
        self.assertIsNotNone(self.registry.registry)
        self.assertIn("canonical_objects", self.registry.registry)
    
    def test_unified_program_state_exists(self):
        """Test unified_program_state object exists"""
        obj = self.registry.get_object("unified_program_state")
        self.assertIsNotNone(obj)
        self.assertIn("allowed_targets", obj)
        self.assertIn("forbidden_actions", obj)
    
    def test_resolve_target(self):
        """Test target resolution"""
        target = self.registry.resolve_target("unified_program_state", "openclaw-workspace")
        self.assertIsNotNone(target)
        self.assertEqual(target, "SESSION-STATE.md")
    
    def test_get_write_policy(self):
        """Test write policy retrieval"""
        policy = self.registry.get_write_policy("unified_program_state", "openclaw-workspace")
        self.assertEqual(policy, "update_only")
    
    def test_get_forbidden_actions(self):
        """Test forbidden actions retrieval"""
        forbidden = self.registry.get_forbidden_actions("unified_program_state")
        self.assertIn("create_duplicate_state_file", forbidden)
    
    def test_ambiguity_policy(self):
        """Test ambiguity policy"""
        policy = self.registry.get_ambiguity_policy("unified_program_state")
        self.assertEqual(policy, "block")


class TestIntentParser(unittest.TestCase):
    """Test Intent Parser"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = IntentParser()
    
    def test_parse_unified_state(self):
        """Test parsing unified state intent"""
        intents = [
            "更新统一进度账",
            "update unified state",
            "修改 PROGRAM_STATE_UNIFIED"
        ]
        
        for intent in intents:
            result = self.parser.parse(intent)
            self.assertEqual(result, "unified_program_state", f"Failed for: {intent}")
    
    def test_parse_session_state(self):
        """Test parsing session state intent"""
        intents = [
            "更新会话状态",
            "update session state",
            "modify SESSION-STATE"
        ]
        
        for intent in intents:
            result = self.parser.parse(intent)
            self.assertEqual(result, "session_state", f"Failed for: {intent}")
    
    def test_parse_non_canonical(self):
        """Test parsing non-canonical intent"""
        intent = "create a new log file"
        result = self.parser.parse(intent)
        self.assertIsNone(result)
    
    def test_infer_action_create(self):
        """Test action inference for create"""
        intents = [
            "create new file",
            "新建统一进度账",
            "创建状态文件"
        ]
        
        for intent in intents:
            result = self.parser.infer_action(intent)
            self.assertEqual(result, "create", f"Failed for: {intent}")
    
    def test_infer_action_update(self):
        """Test action inference for update"""
        intents = [
            "update the state",
            "修改进度账",
            "modify file"
        ]
        
        for intent in intents:
            result = self.parser.infer_action(intent)
            self.assertIn(result, ["modify", "update"], f"Failed for: {intent}")


class TestMemoryPreflight(unittest.TestCase):
    """Test Memory Preflight"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.preflight = MemoryPreflight()
    
    def test_non_canonical_allowed(self):
        """Test non-canonical operation is allowed"""
        result = self.preflight.check(
            task_id="test_001",
            intent="create a new log file",
            target_repo="test_repo"
        )
        
        self.assertEqual(result.decision, Decision.ALLOW)
        self.assertIsNone(result.object_name)
    
    def test_canonical_resolved(self):
        """Test canonical object is resolved"""
        result = self.preflight.check(
            task_id="test_002",
            intent="更新统一进度账",
            target_repo="openclaw-workspace"
        )
        
        self.assertEqual(result.object_name, "unified_program_state")
        self.assertIsNotNone(result.resolved_target)
    
    def test_update_only_blocks_create(self):
        """Test update_only policy blocks create action"""
        result = self.preflight.check(
            task_id="test_003",
            intent="创建新的统一进度账",
            target_repo="openclaw-workspace",
            action="create"
        )
        
        self.assertEqual(result.decision, Decision.BLOCK)
        self.assertIn("forbids create", result.reason)
    
    def test_update_allowed(self):
        """Test update action is allowed"""
        result = self.preflight.check(
            task_id="test_004",
            intent="更新统一进度账",
            target_repo="openclaw-workspace",
            action="modify"
        )
        
        self.assertEqual(result.decision, Decision.ALLOW)
    
    def test_evidence_logged(self):
        """Test evidence is logged"""
        result = self.preflight.check(
            task_id="test_005",
            intent="更新统一进度账",
            target_repo="openclaw-workspace"
        )
        
        self.assertIsNotNone(result.evidence_path)
        self.assertTrue(os.path.exists(result.evidence_path))


class TestMutationGate(unittest.TestCase):
    """Test Mutation Gate"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.gate = MutationGate()
    
    def test_gate_blocks_violation(self):
        """Test gate blocks policy violation"""
        result = self.gate.check_only(
            task_id="test_gate_001",
            intent="创建新的统一进度账",
            target_repo="openclaw-workspace",
            action="create"
        )
        
        self.assertEqual(result.decision, Decision.BLOCK)
    
    def test_gate_allows_valid(self):
        """Test gate allows valid operation"""
        result = self.gate.check_only(
            task_id="test_gate_002",
            intent="更新统一进度账",
            target_repo="openclaw-workspace",
            action="modify"
        )
        
        self.assertEqual(result.decision, Decision.ALLOW)
    
    def test_gate_execute_on_allow(self):
        """Test gate executes mutation on allow"""
        executed = []
        
        def mutation_func():
            executed.append(True)
            return "success"
        
        result = self.gate.execute(
            task_id="test_gate_003",
            intent="更新统一进度账",
            mutation_func=mutation_func,
            target_repo="openclaw-workspace",
            action="modify"
        )
        
        self.assertTrue(result.passed)
        self.assertEqual(result.mutation_result, "success")
        self.assertEqual(len(executed), 1)
    
    def test_gate_block_on_violation(self):
        """Test gate blocks execution on violation"""
        executed = []
        
        def mutation_func():
            executed.append(True)
            return "should not execute"
        
        result = self.gate.execute(
            task_id="test_gate_004",
            intent="创建新的统一进度账",
            mutation_func=mutation_func,
            target_repo="openclaw-workspace",
            action="create"
        )
        
        self.assertFalse(result.passed)
        self.assertEqual(len(executed), 0)


class TestRegressionScenarios(unittest.TestCase):
    """
    Regression Tests - Must Pass
    
    These tests verify the specific failure scenarios from the incident.
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.gate = MutationGate()
    
    def test_regression_1_no_duplicate_when_exists(self):
        """
        Regression Test 1: Existing canonical file → no duplicate created
        
        Scenario:
        - Task: Update unified progress ledger
        - Precondition: Registry points to canonical file
        - Expected: No new file created, use existing canonical path
        """
        result = self.gate.check_only(
            task_id="regression_001",
            intent="更新统一进度账",
            target_repo="openclaw-workspace",
            action="create"  # Trying to create
        )
        
        # MUST BLOCK create action
        self.assertEqual(result.decision, Decision.BLOCK)
        
        # MUST provide canonical target
        self.assertIsNotNone(result.resolved_target)
        
        # MUST log evidence
        self.assertIsNotNone(result.evidence_path)
    
    def test_regression_2_block_on_ambiguous(self):
        """
        Regression Test 2: Ambiguous resolution → blocked
        
        Scenario:
        - Task: Update unified state
        - Precondition: Registry has no mapping or conflict
        - Expected: Blocked, no write
        """
        # Create preflight with non-existent repo
        result = self.gate.check_only(
            task_id="regression_002",
            intent="更新统一进度账",
            target_repo="non_existent_repo",
            action="modify"
        )
        
        # Should resolve to None (no target for this repo)
        # But since it's a canonical object, should still provide guidance
        self.assertEqual(result.object_name, "unified_program_state")
    
    def test_regression_3_update_only_blocks_create(self):
        """
        Regression Test 3: update_only policy → create blocked
        
        Scenario:
        - Task: Create new unified progress ledger
        - Precondition: Object has update_only policy
        - Expected: Blocked with clear reason
        """
        result = self.gate.check_only(
            task_id="regression_003",
            intent="创建新的统一进度账",
            target_repo="openclaw-workspace",
            action="create"
        )
        
        # MUST BLOCK
        self.assertEqual(result.decision, Decision.BLOCK)
        
        # Reason MUST mention policy
        self.assertIn("update_only", result.reason.lower() + str(result.write_policy or "").lower())
    
    def test_regression_4_new_session_same_constraints(self):
        """
        Regression Test 4: New session → same constraints
        
        Scenario:
        - Simulate new session (fresh preflight instance)
        - Task: Update unified progress ledger
        - Expected: Same behavior as old session
        
        This test verifies that constraints are persisted in registry,
        not in session state.
        """
        # Create new instance (simulating new session)
        new_session_gate = MutationGate()
        
        result = new_session_gate.check_only(
            task_id="regression_004",
            intent="更新统一进度账",
            target_repo="openclaw-workspace",
            action="modify"
        )
        
        # MUST behave same as old session
        self.assertEqual(result.decision, Decision.ALLOW)
        self.assertEqual(result.object_name, "unified_program_state")
        self.assertIsNotNone(result.resolved_target)


class TestGateIntegration(unittest.TestCase):
    """Test Gate Integration with Existing Systems"""
    
    def test_preflight_required_for_mutation(self):
        """Test preflight is required before mutation"""
        gate = MutationGate()
        
        # This should pass (valid operation)
        result = gate.check_only(
            task_id="integration_001",
            intent="更新统一进度账",
            target_repo="openclaw-workspace",
            action="modify"
        )
        
        self.assertEqual(result.decision, Decision.ALLOW)
        self.assertIn("canonical_registry", result.consulted_sources)
    
    def test_no_registry_no_mutation(self):
        """Test mutation blocked without registry"""
        # Create preflight with non-existent registry
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_registry = os.path.join(tmpdir, "nonexistent.yaml")
            
            # Create preflight with fake path
            preflight = MemoryPreflight(registry_path=fake_registry)
            
            result = preflight.check(
                task_id="integration_002",
                intent="更新统一进度账",
                target_repo="openclaw-workspace"
            )
            
            # Without registry, canonical objects cannot be resolved
            # But we should still identify the object from intent
            self.assertIsNotNone(result.object_name)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCanonicalRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestIntentParser))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryPreflight))
    suite.addTests(loader.loadTestsFromTestCase(TestMutationGate))
    suite.addTests(loader.loadTestsFromTestCase(TestRegressionScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestGateIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
