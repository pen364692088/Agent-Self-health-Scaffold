"""
Tests for Success Verification - 6 Layer Verification

Tests the core verification logic that prevents false completion claims.

Author: Autonomy Closure
Created: 2026-03-16
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from core.verification.success_verification import (
    SuccessVerifier,
    VerificationLayer,
    VerificationResult,
    create_success_verifier,
)


class TestVerificationLayer:
    """Tests for VerificationLayer dataclass"""
    
    def test_layer_creation(self):
        """Test layer can be created with all fields"""
        layer = VerificationLayer(
            name="L1_exit_code",
            passed=True,
            details="Exit code: 0",
            evidence="exit_code=0",
        )
        assert layer.name == "L1_exit_code"
        assert layer.passed is True
        assert layer.details == "Exit code: 0"
        assert layer.evidence == "exit_code=0"
    
    def test_layer_optional_evidence(self):
        """Test layer can be created without evidence"""
        layer = VerificationLayer(
            name="L2_artifacts",
            passed=False,
            details="Missing files",
        )
        assert layer.evidence is None


class TestVerificationResult:
    """Tests for VerificationResult dataclass"""
    
    def test_result_to_dict(self):
        """Test result serialization"""
        layers = [
            VerificationLayer(name="L1_exit_code", passed=True, details="OK"),
            VerificationLayer(name="L2_artifacts", passed=False, details="Missing"),
        ]
        result = VerificationResult(
            task_id="test_task_001",
            layers=layers,
            all_passed=False,
            timestamp=datetime(2026, 3, 16, 12, 0, 0, tzinfo=timezone.utc),
        )
        
        data = result.to_dict()
        assert data["task_id"] == "test_task_001"
        assert data["all_passed"] is False
        assert len(data["layers"]) == 2
        assert data["layers"][0]["name"] == "L1_exit_code"
        assert data["layers"][1]["passed"] is False


class TestSuccessVerifierLayer1:
    """Tests for L1: Exit Code Verification"""
    
    def test_exit_code_zero_passes(self):
        """Exit code 0 should pass"""
        verifier = create_success_verifier()
        layer = verifier.verify_layer_1_exit_code(0)
        
        assert layer.name == "L1_exit_code"
        assert layer.passed is True
        assert "0" in layer.details
    
    def test_exit_code_nonzero_fails(self):
        """Non-zero exit code should fail"""
        verifier = create_success_verifier()
        layer = verifier.verify_layer_1_exit_code(1)
        
        assert layer.passed is False
        assert "1" in layer.details
    
    def test_exit_code_negative_fails(self):
        """Negative exit code should fail"""
        verifier = create_success_verifier()
        layer = verifier.verify_layer_1_exit_code(-1)
        
        assert layer.passed is False


class TestSuccessVerifierLayer2:
    """Tests for L2: Artifact Verification"""
    
    def test_all_artifacts_present_passes(self):
        """All artifacts present should pass"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create expected files
            Path(tmpdir, "file1.txt").write_text("content")
            Path(tmpdir, "file2.json").write_text("{}")
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_2_artifacts(["file1.txt", "file2.json"])
            
            assert layer.passed is True
            assert "Missing: 0" in layer.details
    
    def test_missing_artifact_fails(self):
        """Missing artifact should fail"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "exists.txt").write_text("content")
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_2_artifacts(["exists.txt", "missing.txt"])
            
            assert layer.passed is False
            assert "missing.txt" in layer.evidence
    
    def test_empty_artifact_list_passes(self):
        """Empty artifact list should pass"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_2_artifacts([])
            
            assert layer.passed is True


class TestSuccessVerifierLayer3:
    """Tests for L3: Contract Verification"""
    
    def test_all_conditions_satisfied_passes(self):
        """All conditions satisfied should pass"""
        verifier = create_success_verifier()
        conditions = [
            {"name": "cond_1", "satisfied": True},
            {"name": "cond_2", "satisfied": True},
        ]
        layer = verifier.verify_layer_3_contract(conditions)
        
        assert layer.passed is True
        assert "Failed: 0" in layer.details
    
    def test_unsatisfied_condition_fails(self):
        """Unsatisfied condition should fail"""
        verifier = create_success_verifier()
        conditions = [
            {"name": "cond_1", "satisfied": True},
            {"name": "cond_2", "satisfied": False},
        ]
        layer = verifier.verify_layer_3_contract(conditions)
        
        assert layer.passed is False
        assert "cond_2" in layer.evidence
    
    def test_empty_conditions_passes(self):
        """Empty conditions should pass"""
        verifier = create_success_verifier()
        layer = verifier.verify_layer_3_contract([])
        
        assert layer.passed is True


class TestSuccessVerifierLayer4:
    """Tests for L4: Content Verification"""
    
    def test_content_size_check_passes(self):
        """Content with sufficient size should pass"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "data.json").write_text('{"key": "value"}')
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_4_content("data.json", min_size=5)
            
            assert layer.passed is True
    
    def test_content_size_check_fails(self):
        """Content with insufficient size should fail"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "small.txt").write_text("x")
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_4_content("small.txt", min_size=100)
            
            assert layer.passed is False
            assert "min_size" in layer.details
    
    def test_content_missing_keys_fails(self):
        """Content missing required keys should fail"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "partial.json").write_text('{"a": 1}')
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_4_content(
                "partial.json",
                required_keys=["a", "b", "c"],
            )
            
            assert layer.passed is False
            assert "Missing keys" in layer.details
    
    def test_content_all_keys_present_passes(self):
        """Content with all required keys should pass"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "complete.json").write_text('{"a": 1, "b": 2, "c": 3}')
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_4_content(
                "complete.json",
                required_keys=["a", "b", "c"],
            )
            
            assert layer.passed is True
    
    def test_nonexistent_artifact_fails(self):
        """Nonexistent artifact should fail"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_4_content("nonexistent.json")
            
            assert layer.passed is False
            assert "not found" in layer.details


class TestSuccessVerifierLayer5:
    """Tests for L5: Consistency Verification"""
    
    def test_consistency_all_present_passes(self):
        """All three artifacts present should pass"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create task_state.json
            Path(tmpdir, "task_state.json").write_text(json.dumps({
                "status": "completed",
                "task_id": "test_001",
            }))
            
            # Create ledger.jsonl
            Path(tmpdir, "ledger.jsonl").write_text(
                '{"event": "start"}\n{"event": "end"}\n'
            )
            
            # Create evidence directory with file
            evidence_dir = Path(tmpdir, "evidence")
            evidence_dir.mkdir()
            (evidence_dir / "proof.txt").write_text("evidence")
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_5_consistency(
                task_id="test_001",
                task_state_path="task_state.json",
                ledger_path="ledger.jsonl",
                evidence_dir="evidence",
            )
            
            assert layer.passed is True
    
    def test_consistency_missing_state_fails(self):
        """Missing task_state.json should fail"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "ledger.jsonl").write_text('{}\n')
            Path(tmpdir, "evidence").mkdir()
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_5_consistency(
                task_id="test_001",
                task_state_path="task_state.json",
                ledger_path="ledger.jsonl",
                evidence_dir="evidence",
            )
            
            assert layer.passed is False
            assert "task_state.json missing" in layer.details
    
    def test_consistency_incomplete_status_fails(self):
        """Non-completed status should fail"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "task_state.json").write_text(json.dumps({
                "status": "in_progress",
            }))
            Path(tmpdir, "ledger.jsonl").write_text('{}\n')
            Path(tmpdir, "evidence").mkdir()
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_5_consistency(
                task_id="test_001",
                task_state_path="task_state.json",
                ledger_path="ledger.jsonl",
                evidence_dir="evidence",
            )
            
            assert layer.passed is False
            assert "in_progress" in layer.details


class TestSuccessVerifierLayer6:
    """Tests for L6: Event Verification"""
    
    def test_event_found_passes(self):
        """Found task_completed event should pass"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir, "events.jsonl")
            events_file.write_text(
                '{"type": "task_started", "task_id": "test_001"}\n'
                '{"type": "task_completed", "task_id": "test_001", "timestamp": "2026-03-16T12:00:00Z"}\n'
            )
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_6_event(
                task_id="test_001",
                events_path="events.jsonl",
            )
            
            assert layer.passed is True
            assert "task_completed event found" in layer.details
    
    def test_event_not_found_fails(self):
        """Missing task_completed event should fail"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir, "events.jsonl")
            events_file.write_text(
                '{"type": "task_started", "task_id": "test_001"}\n'
            )
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_6_event(
                task_id="test_001",
                events_path="events.jsonl",
            )
            
            assert layer.passed is False
            assert "not found" in layer.details
    
    def test_event_wrong_task_id_fails(self):
        """Event for wrong task ID should fail"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir, "events.jsonl")
            events_file.write_text(
                '{"type": "task_completed", "task_id": "other_task"}\n'
            )
            
            verifier = create_success_verifier(base_path=tmpdir)
            layer = verifier.verify_layer_6_event(
                task_id="test_001",
                events_path="events.jsonl",
            )
            
            assert layer.passed is False


class TestSuccessVerifierFullVerify:
    """Tests for full 6-layer verification"""
    
    def test_full_verify_all_pass(self):
        """All layers passing should return all_passed=True"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup artifacts
            Path(tmpdir, "output.txt").write_text("result")
            Path(tmpdir, "task_state.json").write_text(json.dumps({"status": "completed"}))
            Path(tmpdir, "ledger.jsonl").write_text('{}\n')
            evidence_dir = Path(tmpdir, "evidence")
            evidence_dir.mkdir()
            (evidence_dir / "proof.txt").write_text("proof")
            Path(tmpdir, "events.jsonl").write_text(
                '{"type": "task_completed", "task_id": "test_001"}\n'
            )
            
            verifier = create_success_verifier(base_path=tmpdir)
            result = verifier.verify(
                task_id="test_001",
                exit_code=0,
                expected_files=["output.txt"],
                events_path="events.jsonl",
            )
            
            assert result.all_passed is True
            assert len(result.layers) == 6
    
    def test_full_verify_partial_fail(self):
        """Some layers failing should return all_passed=False"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Only minimal setup
            Path(tmpdir, "task_state.json").write_text(json.dumps({"status": "completed"}))
            Path(tmpdir, "ledger.jsonl").write_text('{}\n')
            Path(tmpdir, "evidence").mkdir()
            
            verifier = create_success_verifier(base_path=tmpdir)
            result = verifier.verify(
                task_id="test_001",
                exit_code=1,  # Fail L1
                expected_files=["missing.txt"],  # Fail L2
            )
            
            assert result.all_passed is False
            # L1 and L2 should fail
            l1 = next(l for l in result.layers if l.name == "L1_exit_code")
            l2 = next(l for l in result.layers if l.name == "L2_artifacts")
            assert l1.passed is False
            assert l2.passed is False


class TestSuccessVerifierStats:
    """Tests for statistics tracking"""
    
    def test_stats_empty(self):
        """Empty verifier should have zero stats"""
        verifier = create_success_verifier()
        stats = verifier.get_stats()
        
        assert stats["total"] == 0
        assert stats["false_positive_rate"] == 0
    
    def test_stats_after_verification(self):
        """Stats should reflect verification history"""
        verifier = create_success_verifier()
        
        # Add some results manually
        verifier._verification_history.append(VerificationResult(
            task_id="test_1",
            layers=[
                VerificationLayer(name="L1", passed=True, details="OK"),
            ],
            all_passed=True,
            timestamp=datetime.now(timezone.utc),
        ))
        verifier._verification_history.append(VerificationResult(
            task_id="test_2",
            layers=[
                VerificationLayer(name="L1", passed=True, details="OK"),
                VerificationLayer(name="L2", passed=False, details="Missing"),
            ],
            all_passed=False,
            timestamp=datetime.now(timezone.utc),
        ))
        
        stats = verifier.get_stats()
        assert stats["total"] == 2
        assert stats["passed"] == 1
        assert stats["failed"] == 1
    
    def test_false_positive_detection(self):
        """Should detect false positives (L1 passed but other layers failed)"""
        verifier = create_success_verifier()
        
        # False positive: L1 passed, L2 failed
        verifier._verification_history.append(VerificationResult(
            task_id="false_pos",
            layers=[
                VerificationLayer(name="L1_exit_code", passed=True, details="OK"),
                VerificationLayer(name="L2_artifacts", passed=False, details="Missing"),
            ],
            all_passed=False,
            timestamp=datetime.now(timezone.utc),
        ))
        
        stats = verifier.get_stats()
        assert stats["false_positive_count"] == 1
        assert stats["false_positive_rate"] == 1.0


class TestSuccessVerifierContract:
    """Tests for SUCCESS_VERIFICATION_POLICY contract compliance"""
    
    def test_never_rely_on_exit_code_alone(self):
        """Verifier must never rely on exit code alone"""
        # This test verifies the contract: L1 alone is not sufficient
        with tempfile.TemporaryDirectory() as tmpdir:
            # Good exit code but missing artifacts
            verifier = create_success_verifier(base_path=tmpdir)
            result = verifier.verify(
                task_id="test_contract",
                exit_code=0,
                expected_files=["missing_file.txt"],
            )
            
            # Exit code 0 but verification should fail
            assert result.layers[0].passed is True  # L1 passes
            assert result.all_passed is False  # But overall fails
            assert "禁止只靠 exit code 判定成功" in SuccessVerifier.__doc__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
