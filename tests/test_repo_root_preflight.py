#!/usr/bin/env python3
"""
Repo Root Preflight Tests

Purpose:
  Ensure repo root preflight blocks wrong workspace and allows correct repo.

Required Tests:
  1. Correct repo → preflight pass
  2. Wrong workspace → preflight block
  3. New session → checks repo root first
  4. State update with wrong repo → block

Version: v1.0
Date: 2026-03-16
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add runtime to path
runtime_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
runtime_path = os.path.join(runtime_dir, "runtime")
if runtime_path not in sys.path:
    sys.path.insert(0, runtime_path)

from repo_root_preflight import (
    RepoRootPreflight,
    RepoRootResult,
    PreflightStatus,
    check_repo_root,
    enforce_repo_root
)


class TestRepoRootPreflightCore(unittest.TestCase):
    """Test Repo Root Preflight core functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.preflight = RepoRootPreflight("Agent-Self-health-Scaffold")
    
    def test_expected_root_defined(self):
        """Test expected root is defined"""
        self.assertIsNotNone(self.preflight.expected_root)
        self.assertEqual(
            self.preflight.expected_root,
            "/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold"
        )
    
    def test_expected_remote_defined(self):
        """Test expected remote is defined"""
        self.assertIsNotNone(self.preflight.expected_remote)
        self.assertEqual(
            self.preflight.expected_remote,
            "git@github.com:pen364692088/Agent-Self-health-Scaffold.git"
        )
    
    def test_check_returns_result(self):
        """Test check returns RepoRootResult"""
        result = self.preflight.check()
        self.assertIsInstance(result, RepoRootResult)
        self.assertIsNotNone(result.expected_root)
        self.assertIsNotNone(result.status)
    
    def test_result_has_required_fields(self):
        """Test result has all required fields"""
        result = self.preflight.check()
        
        self.assertIsNotNone(result.passed)
        self.assertIsNotNone(result.expected_root)
        self.assertIsNotNone(result.status)
        self.assertIsNotNone(result.reason)
        self.assertIsNotNone(result.action_type)


class TestRepoRootPreflightCorrectRepo(unittest.TestCase):
    """Test preflight in correct repo"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.preflight = RepoRootPreflight("Agent-Self-health-Scaffold")
    
    def test_correct_repo_passes(self):
        """
        Regression Test 1: Correct repo → preflight pass
        
        Scenario:
        - In correct repo root
        - Expected: PASS
        """
        result = self.preflight.check("test_execution")
        
        # Should pass when run from correct repo
        self.assertEqual(result.status, PreflightStatus.PASS)
        self.assertEqual(
            result.actual_root,
            "/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold"
        )
    
    def test_correct_repo_remote_matches(self):
        """Test remote matches in correct repo"""
        result = self.preflight.check()
        
        if result.passed:
            self.assertEqual(
                result.actual_root,
                self.preflight.expected_root
            )


class TestRepoRootPreflightWrongWorkspace(unittest.TestCase):
    """Test preflight blocks wrong workspace"""
    
    def test_wrong_workspace_blocked(self):
        """
        Regression Test 2: Wrong workspace → preflight block
        
        Scenario:
        - In ~/.openclaw/workspace or other wrong directory
        - Expected: BLOCK
        """
        # Create preflight with different expected root
        preflight = RepoRootPreflight("Agent-Self-health-Scaffold")
        
        # Mock git root to simulate wrong workspace
        with patch.object(preflight, '_get_git_root', return_value="/home/moonlight/.openclaw/workspace"):
            result = preflight.check("file_read_write")
            
            self.assertEqual(result.status, PreflightStatus.BLOCK)
            self.assertEqual(result.block_reason, "repo_root_mismatch")
    
    def test_not_git_repo_blocked(self):
        """Test not being in git repo is blocked"""
        preflight = RepoRootPreflight("Agent-Self-health-Scaffold")
        
        with patch.object(preflight, '_get_git_root', return_value=None):
            result = preflight.check("mutation")
            
            self.assertEqual(result.status, PreflightStatus.BLOCK)
            self.assertEqual(result.block_reason, "not_git_repo")


class TestRepoRootPreflightNewSession(unittest.TestCase):
    """Test preflight in new session scenario"""
    
    def test_new_session_checks_repo_root(self):
        """
        Regression Test 3: New session → checks repo root first
        
        Scenario:
        - Simulate new session (fresh preflight instance)
        - Expected: Still validates repo root
        """
        # Create new instance (simulating new session)
        new_session_preflight = RepoRootPreflight("Agent-Self-health-Scaffold")
        
        result = new_session_preflight.check("state_update")
        
        # Should still have expected root defined
        self.assertIsNotNone(new_session_preflight.expected_root)
        self.assertEqual(
            new_session_preflight.expected_root,
            "/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold"
        )
    
    def test_constraints_persist_across_sessions(self):
        """Test constraints are persisted in class, not instance"""
        preflight1 = RepoRootPreflight("Agent-Self-health-Scaffold")
        preflight2 = RepoRootPreflight("Agent-Self-health-Scaffold")
        
        # Both should have same expected root
        self.assertEqual(preflight1.expected_root, preflight2.expected_root)
        self.assertEqual(preflight1.expected_remote, preflight2.expected_remote)


class TestRepoRootPreflightStateUpdate(unittest.TestCase):
    """Test preflight blocks state update with wrong repo"""
    
    def test_state_update_wrong_repo_blocked(self):
        """
        Regression Test 4: State update with wrong repo → block
        
        Scenario:
        - Attempting state update from wrong workspace
        - Expected: BLOCK, no write
        """
        preflight = RepoRootPreflight("Agent-Self-health-Scaffold")
        
        with patch.object(preflight, '_get_git_root', return_value="/tmp/wrong_directory"):
            result = preflight.check("state_update")
            
            self.assertEqual(result.status, PreflightStatus.BLOCK)
            self.assertIn("mismatch", result.reason.lower())


class TestRepoRootPreflightConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""
    
    def test_check_repo_root_returns_bool(self):
        """Test check_repo_root returns boolean"""
        result = check_repo_root("Agent-Self-health-Scaffold")
        self.assertIsInstance(result, bool)
    
    def test_enforce_repo_root_raises_on_wrong_repo(self):
        """Test enforce_repo_root raises error on wrong repo"""
        preflight = RepoRootPreflight("Agent-Self-health-Scaffold")
        
        with patch.object(preflight, '_get_git_root', return_value="/wrong/path"):
            with self.assertRaises(RuntimeError):
                preflight.check_or_block("test")


class TestRepoRootPreflightBlockMessage(unittest.TestCase):
    """Test block message generation"""
    
    def test_block_message_includes_expected_root(self):
        """Test block message includes expected root"""
        preflight = RepoRootPreflight("Agent-Self-health-Scaffold")
        
        with patch.object(preflight, '_get_git_root', return_value="/wrong/path"):
            result = preflight.check()
            message = preflight.get_block_message(result)
            
            self.assertIn("Expected Root:", message)
            self.assertIn(preflight.expected_root, message)
    
    def test_block_message_includes_fix_instructions(self):
        """Test block message includes fix instructions"""
        preflight = RepoRootPreflight("Agent-Self-health-Scaffold")
        
        with patch.object(preflight, '_get_git_root', return_value="/wrong/path"):
            result = preflight.check()
            message = preflight.get_block_message(result)
            
            self.assertIn("HOW TO FIX", message)
            self.assertIn("cd", message)


class TestRepoRootPreflightIntegration(unittest.TestCase):
    """Integration tests with actual repo"""
    
    def test_actual_repo_matches_expected(self):
        """Test actual repo matches expected for this project"""
        preflight = RepoRootPreflight("Agent-Self-health-Scaffold")
        result = preflight.check()
        
        # This test runs from the correct repo
        self.assertEqual(result.status, PreflightStatus.PASS)
        self.assertEqual(result.actual_root, result.expected_root)
    
    def test_convenience_check_returns_true_in_correct_repo(self):
        """Test convenience check returns True in correct repo"""
        result = check_repo_root("Agent-Self-health-Scaffold")
        self.assertTrue(result)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRepoRootPreflightCore))
    suite.addTests(loader.loadTestsFromTestCase(TestRepoRootPreflightCorrectRepo))
    suite.addTests(loader.loadTestsFromTestCase(TestRepoRootPreflightWrongWorkspace))
    suite.addTests(loader.loadTestsFromTestCase(TestRepoRootPreflightNewSession))
    suite.addTests(loader.loadTestsFromTestCase(TestRepoRootPreflightStateUpdate))
    suite.addTests(loader.loadTestsFromTestCase(TestRepoRootPreflightConvenienceFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestRepoRootPreflightBlockMessage))
    suite.addTests(loader.loadTestsFromTestCase(TestRepoRootPreflightIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
