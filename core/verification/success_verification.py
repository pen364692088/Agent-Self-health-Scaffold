"""
Success Verification - Minimal Implementation

6层成功验证，防止假完成。

Author: Autonomy Closure
Created: 2026-03-16
Version: 1.0.0-minimal
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import json
import os


@dataclass
class VerificationLayer:
    """验证层结果"""
    name: str
    passed: bool
    details: str
    evidence: Optional[str] = None


@dataclass
class VerificationResult:
    """验证结果"""
    task_id: str
    layers: List[VerificationLayer]
    all_passed: bool
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "layers": [
                {
                    "name": l.name,
                    "passed": l.passed,
                    "details": l.details,
                    "evidence": l.evidence,
                }
                for l in self.layers
            ],
            "all_passed": self.all_passed,
            "timestamp": self.timestamp.isoformat(),
        }


class SuccessVerifier:
    """
    成功验证器
    
    基于 SUCCESS_VERIFICATION_POLICY.md 中定义的 6 层验证。
    
    ⚠️ 禁止只靠 exit code 判定成功
    """
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self._verification_history: List[VerificationResult] = []
    
    def verify_layer_1_exit_code(self, exit_code: int) -> VerificationLayer:
        """L1: Exit code 检查"""
        passed = exit_code == 0
        return VerificationLayer(
            name="L1_exit_code",
            passed=passed,
            details=f"Exit code: {exit_code}",
            evidence=f"exit_code={exit_code}",
        )
    
    def verify_layer_2_artifacts(
        self,
        expected_files: List[str],
    ) -> VerificationLayer:
        """L2: 产物存在检查"""
        missing = []
        for file in expected_files:
            full_path = self.base_path / file
            if not full_path.exists():
                missing.append(file)
        
        passed = len(missing) == 0
        details = f"Expected: {len(expected_files)}, Missing: {len(missing)}"
        
        return VerificationLayer(
            name="L2_artifacts",
            passed=passed,
            details=details,
            evidence=f"missing={missing}" if missing else "all_present",
        )
    
    def verify_layer_3_contract(
        self,
        conditions: List[Dict[str, Any]],
    ) -> VerificationLayer:
        """L3: Contract 条件检查"""
        failed = []
        for i, cond in enumerate(conditions):
            if not cond.get("satisfied", False):
                failed.append(cond.get("name", f"condition_{i}"))
        
        passed = len(failed) == 0
        details = f"Conditions: {len(conditions)}, Failed: {len(failed)}"
        
        return VerificationLayer(
            name="L3_contract",
            passed=passed,
            details=details,
            evidence=f"failed={failed}" if failed else "all_satisfied",
        )
    
    def verify_layer_4_content(
        self,
        artifact_path: str,
        required_keys: Optional[List[str]] = None,
        min_size: int = 0,
    ) -> VerificationLayer:
        """L4: 内容检查"""
        full_path = self.base_path / artifact_path
        
        if not full_path.exists():
            return VerificationLayer(
                name="L4_content",
                passed=False,
                details=f"Artifact not found: {artifact_path}",
            )
        
        # 检查大小
        size = full_path.stat().st_size
        if size < min_size:
            return VerificationLayer(
                name="L4_content",
                passed=False,
                details=f"Size {size} < min_size {min_size}",
            )
        
        # 检查必需键（如果是 JSON）
        if required_keys and full_path.suffix == ".json":
            try:
                with open(full_path) as f:
                    content = json.load(f)
                
                missing_keys = [k for k in required_keys if k not in content]
                if missing_keys:
                    return VerificationLayer(
                        name="L4_content",
                        passed=False,
                        details=f"Missing keys: {missing_keys}",
                    )
            except Exception as e:
                return VerificationLayer(
                    name="L4_content",
                    passed=False,
                    details=f"JSON parse error: {e}",
                )
        
        return VerificationLayer(
            name="L4_content",
            passed=True,
            details=f"Size: {size}, Valid: True",
            evidence=f"size={size}",
        )
    
    def verify_layer_5_consistency(
        self,
        task_id: str,
        task_state_path: str,
        ledger_path: str,
        evidence_dir: str,
    ) -> VerificationLayer:
        """L5: 三件套一致性检查"""
        state_path = self.base_path / task_state_path
        ledger_full = self.base_path / ledger_path
        evidence_full = self.base_path / evidence_dir
        
        issues = []
        
        # 检查 state
        if not state_path.exists():
            issues.append("task_state.json missing")
        else:
            try:
                with open(state_path) as f:
                    state = json.load(f)
                if state.get("status") != "completed":
                    issues.append(f"state.status={state.get('status')}")
            except Exception as e:
                issues.append(f"state parse error: {e}")
        
        # 检查 ledger
        if not ledger_full.exists():
            issues.append("ledger.jsonl missing")
        
        # 检查 evidence
        if not evidence_full.exists():
            issues.append("evidence directory missing")
        elif not list(evidence_full.glob("*")):
            issues.append("evidence directory empty")
        
        passed = len(issues) == 0
        details = f"Consistency: {'OK' if passed else ', '.join(issues)}"
        
        return VerificationLayer(
            name="L5_consistency",
            passed=passed,
            details=details,
            evidence="consistent" if passed else f"issues={issues}",
        )
    
    def verify_layer_6_event(
        self,
        task_id: str,
        events_path: str,
    ) -> VerificationLayer:
        """L6: task_completed 事件检查"""
        events_full = self.base_path / events_path
        
        if not events_full.exists():
            return VerificationLayer(
                name="L6_event",
                passed=False,
                details="Events file missing",
            )
        
        try:
            with open(events_full) as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        if (
                            event.get("type") == "task_completed"
                            and event.get("task_id") == task_id
                        ):
                            return VerificationLayer(
                                name="L6_event",
                                passed=True,
                                details="task_completed event found",
                                evidence=event.get("timestamp"),
                            )
        except Exception as e:
            return VerificationLayer(
                name="L6_event",
                passed=False,
                details=f"Events parse error: {e}",
            )
        
        return VerificationLayer(
            name="L6_event",
            passed=False,
            details="task_completed event not found",
        )
    
    def verify(
        self,
        task_id: str,
        exit_code: int,
        expected_files: List[str],
        contract_conditions: Optional[List[Dict[str, Any]]] = None,
        content_artifact: Optional[str] = None,
        content_required_keys: Optional[List[str]] = None,
        task_state_path: str = "task_state.json",
        ledger_path: str = "ledger.jsonl",
        evidence_dir: str = "evidence",
        events_path: str = "events.jsonl",
    ) -> VerificationResult:
        """
        执行完整 6 层验证
        
        Args:
            task_id: 任务 ID
            exit_code: 命令退出码
            expected_files: 预期产物文件
            contract_conditions: Contract 条件
            content_artifact: 内容检查的产物
            content_required_keys: 必需的键
            task_state_path: task_state.json 路径
            ledger_path: ledger.jsonl 路径
            evidence_dir: evidence 目录
            events_path: events.jsonl 路径
        
        Returns:
            VerificationResult
        """
        layers = []
        
        # L1: Exit code
        layers.append(self.verify_layer_1_exit_code(exit_code))
        
        # L2: Artifacts
        layers.append(self.verify_layer_2_artifacts(expected_files))
        
        # L3: Contract
        if contract_conditions:
            layers.append(self.verify_layer_3_contract(contract_conditions))
        else:
            layers.append(VerificationLayer(
                name="L3_contract",
                passed=True,
                details="No contract conditions specified",
            ))
        
        # L4: Content
        if content_artifact:
            layers.append(self.verify_layer_4_content(
                content_artifact,
                content_required_keys,
            ))
        else:
            layers.append(VerificationLayer(
                name="L4_content",
                passed=True,
                details="No content validation specified",
            ))
        
        # L5: Consistency
        layers.append(self.verify_layer_5_consistency(
            task_id,
            task_state_path,
            ledger_path,
            evidence_dir,
        ))
        
        # L6: Event
        layers.append(self.verify_layer_6_event(task_id, events_path))
        
        # 综合判定
        all_passed = all(l.passed for l in layers)
        
        result = VerificationResult(
            task_id=task_id,
            layers=layers,
            all_passed=all_passed,
            timestamp=datetime.now(timezone.utc),
        )
        
        self._verification_history.append(result)
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        total = len(self._verification_history)
        if total == 0:
            return {"total": 0, "passed": 0, "failed": 0, "false_positive_rate": 0}
        
        passed = sum(1 for v in self._verification_history if v.all_passed)
        failed = total - passed
        
        # 检测假完成：L1 passed 但其他层 failed
        false_positives = 0
        for v in self._verification_history:
            l1_passed = any(l.name == "L1_exit_code" and l.passed for l in v.layers)
            other_failed = any(l.name != "L1_exit_code" and not l.passed for l in v.layers)
            if l1_passed and other_failed:
                false_positives += 1
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total,
            "false_positive_count": false_positives,
            "false_positive_rate": false_positives / total if total > 0 else 0,
        }


def create_success_verifier(base_path: str = ".") -> SuccessVerifier:
    """创建成功验证器"""
    return SuccessVerifier(base_path=base_path)
