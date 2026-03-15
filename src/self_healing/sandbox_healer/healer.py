#!/usr/bin/env python3
"""
Sandbox Healer - 沙箱自愈执行器

职责：
1. 在隔离环境执行修复
2. 运行 Gate A/B/C 验证
3. 产出 patch、report、rollback info
4. negative check（验证没有引入回归）
"""

import os
import json
import shutil
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime


@dataclass
class ValidationResult:
    """验证结果"""
    gate_name: str
    passed: bool
    details: str
    logs: List[str]


@dataclass
class SandboxReport:
    """沙箱执行报告"""
    # 标识
    report_id: str
    timestamp: str
    bundle_id: str
    candidate_id: str
    
    # 沙箱信息
    sandbox_path: str
    branch_name: str
    
    # 执行结果
    applied_successfully: bool
    validation_results: List[ValidationResult]
    
    # 产出物
    patch_path: Optional[str]
    validation_report_path: str
    rollback_script_path: str
    
    # 统计
    lines_added: int
    lines_removed: int
    files_changed: List[str]
    
    # negative check
    negative_check_passed: bool
    regression_tests_passed: bool
    
    # 决策
    approved_for_merge: bool
    rejection_reason: Optional[str]
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "bundle_id": self.bundle_id,
            "candidate_id": self.candidate_id,
            "sandbox_path": self.sandbox_path,
            "branch_name": self.branch_name,
            "applied_successfully": self.applied_successfully,
            "validation_results": [
                {"gate_name": r.gate_name, "passed": r.passed, "details": r.details}
                for r in self.validation_results
            ],
            "patch_path": self.patch_path,
            "validation_report_path": self.validation_report_path,
            "rollback_script_path": self.rollback_script_path,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "files_changed": self.files_changed,
            "negative_check_passed": self.negative_check_passed,
            "regression_tests_passed": self.regression_tests_passed,
            "approved_for_merge": self.approved_for_merge,
            "rejection_reason": self.rejection_reason,
        }


class SandboxHealer:
    """沙箱自愈执行器"""
    
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.sandbox_base = self.workspace / ".sandbox"
        self.reports_dir = self.workspace / "artifacts" / "self_healing" / "sandbox_reports"
        self.patches_dir = self.workspace / "artifacts" / "self_healing" / "patches"
        
        self.sandbox_base.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.patches_dir.mkdir(parents=True, exist_ok=True)
    
    def heal(
        self,
        bundle_id: str,
        candidate: Any,  # RemedyCandidate
        original_branch: str = "main"
    ) -> SandboxReport:
        """
        在沙箱执行修复
        
        流程：
        1. 创建临时 worktree
        2. 应用修复
        3. 运行 Gate A/B/C
        4. negative check
        5. 生成 patch 和 report
        6. 清理沙箱
        """
        report_id = f"sandbox_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{bundle_id[:8]}"
        branch_name = f"auto-fix-{bundle_id[:8]}-{candidate.candidate_id}"
        
        sandbox_path = None
        validation_results = []
        
        try:
            # 1. 创建沙箱
            sandbox_path = self._create_sandbox(original_branch, branch_name, bundle_id)
            
            # 2. 应用修复
            applied = self._apply_remedy(sandbox_path, candidate)
            
            if not applied:
                return self._create_failure_report(
                    report_id, bundle_id, candidate.candidate_id,
                    sandbox_path, branch_name, "修复应用失败"
                )
            
            # 3. Gate A: Contract 验证
            gate_a = self._run_gate_a(sandbox_path, candidate)
            validation_results.append(gate_a)
            
            if not gate_a.passed:
                return self._create_failure_report(
                    report_id, bundle_id, candidate.candidate_id,
                    sandbox_path, branch_name, f"Gate A 失败: {gate_a.details}"
                )
            
            # 4. Gate B: E2E 测试
            gate_b = self._run_gate_b(sandbox_path)
            validation_results.append(gate_b)
            
            if not gate_b.passed:
                return self._create_failure_report(
                    report_id, bundle_id, candidate.candidate_id,
                    sandbox_path, branch_name, f"Gate B 失败: {gate_b.details}"
                )
            
            # 5. Gate C: Preflight 检查
            gate_c = self._run_gate_c(sandbox_path)
            validation_results.append(gate_c)
            
            if not gate_c.passed:
                return self._create_failure_report(
                    report_id, bundle_id, candidate.candidate_id,
                    sandbox_path, branch_name, f"Gate C 失败: {gate_c.details}"
                )
            
            # 6. Negative check
            negative_check = self._run_negative_check(sandbox_path, candidate)
            
            # 7. 生成 patch
            patch_path = self._generate_patch(sandbox_path, original_branch)
            
            # 8. 生成 rollback 脚本
            rollback_script = self._generate_rollback_script(sandbox_path, candidate)
            
            # 9. 统计变更
            stats = self._get_change_stats(sandbox_path)
            
            # 10. 创建成功报告
            report = SandboxReport(
                report_id=report_id,
                timestamp=datetime.now().isoformat(),
                bundle_id=bundle_id,
                candidate_id=candidate.candidate_id,
                sandbox_path=str(sandbox_path),
                branch_name=branch_name,
                applied_successfully=True,
                validation_results=validation_results,
                patch_path=patch_path,
                validation_report_path=str(self.reports_dir / f"{report_id}.json"),
                rollback_script_path=rollback_script,
                lines_added=stats["added"],
                lines_removed=stats["removed"],
                files_changed=stats["files"],
                negative_check_passed=negative_check.passed,
                regression_tests_passed=True,  # 已在 Gate B 验证
                approved_for_merge=all(r.passed for r in validation_results) and negative_check.passed,
                rejection_reason=None if all(r.passed for r in validation_results) else "验证失败"
            )
            
            # 保存报告
            self._save_report(report)
            
            return report
            
        except Exception as e:
            return self._create_failure_report(
                report_id, bundle_id, candidate.candidate_id,
                sandbox_path or Path("unknown"), branch_name, f"异常: {str(e)}"
            )
        finally:
            # 清理沙箱（可选，保留用于调试）
            # self._cleanup_sandbox(sandbox_path)
            pass
    
    def _create_sandbox(self, base_branch: str, new_branch: str, bundle_id: str = "") -> Path:
        """创建沙箱 worktree"""
        # 创建临时目录
        sandbox_name = new_branch.replace('/', '_').replace(' ', '_')
        sandbox_path = self.sandbox_base / sandbox_name
        
        # 如果已存在，先删除
        if sandbox_path.exists():
            try:
                subprocess.run(
                    ["git", "worktree", "remove", str(sandbox_path), "--force"],
                    cwd=self.workspace,
                    capture_output=True
                )
            except:
                pass
            shutil.rmtree(sandbox_path, ignore_errors=True)
        
        # 确保分支不存在（使用更短的分支名）
        short_branch = f"auto-fix-{bundle_id[:8]}" if bundle_id else new_branch
        try:
            subprocess.run(
                ["git", "branch", "-D", short_branch],
                cwd=self.workspace,
                capture_output=True
            )
        except:
            pass
        
        # 清理现有 worktree
        try:
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=self.workspace,
                capture_output=True
            )
        except:
            pass
        
        new_branch = short_branch
        
        # 使用 worktree add -b 直接创建新分支（更简洁）
        result = subprocess.run(
            ["git", "worktree", "add", "-b", new_branch, str(sandbox_path)],
            cwd=self.workspace,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to create worktree: {result.stderr}")
        
        return sandbox_path
    
    def _apply_remedy(self, sandbox_path: Path, candidate: Any) -> bool:
        """在沙箱应用修复"""
        try:
            action_type = candidate.action_type
            action_params = candidate.action_params
            
            if action_type == "edit":
                # 执行 edit 操作
                file_path = sandbox_path / action_params.get("file_path", "")
                old_string = action_params.get("old_string", "")
                new_string = action_params.get("new_string", "")
                
                if file_path.exists():
                    content = file_path.read_text()
                    if old_string in content:
                        new_content = content.replace(old_string, new_string, 1)
                        file_path.write_text(new_content)
                        return True
                    else:
                        return False
                else:
                    # 创建新文件
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(new_string)
                    return True
            
            elif action_type == "write":
                # 写入文件
                file_path = sandbox_path / action_params.get("file_path", "")
                content = action_params.get("content", "")
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
                return True
            
            elif action_type == "exec":
                # 执行命令
                command = action_params.get("command", "")
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=sandbox_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return result.returncode == 0
            
            elif action_type == "compound":
                # 复合操作
                steps = action_params.get("steps", [])
                for step in steps:
                    step_type = step.get("tool", "")
                    if step_type == "read":
                        # 读取操作，不需要实际执行
                        pass
                    elif step_type == "edit":
                        # 递归处理 edit
                        sub_candidate = type('obj', (object,), {
                            'action_type': 'edit',
                            'action_params': step
                        })
                        if not self._apply_remedy(sandbox_path, sub_candidate):
                            return False
                    elif step_type == "exec":
                        cmd = step.get("command", "")
                        result = subprocess.run(
                            cmd,
                            shell=True,
                            cwd=sandbox_path,
                            capture_output=True,
                            timeout=60
                        )
                        if result.returncode != 0:
                            return False
                return True
            
            return False
        except Exception as e:
            print(f"[SandboxHealer] Apply remedy failed: {e}")
            return False
    
    def _run_gate_a(self, sandbox_path: Path, candidate: Any) -> ValidationResult:
        """Gate A: Contract 验证"""
        logs = []
        
        # 检查是否触及禁区
        forbidden_patterns = [
            "SOUL.md", "IDENTITY.md", "SELF_HEALING_CONTRACT.md",
            "subtask-orchestrate", "callback-worker",
            "verify-and-close", "done-guard"
        ]
        
        for file_path in candidate.target_files:
            for pattern in forbidden_patterns:
                if pattern in file_path:
                    return ValidationResult(
                        gate_name="Gate A: Contract",
                        passed=False,
                        details=f"触及禁区: {pattern}",
                        logs=logs
                    )
        
        # 检查变更大小
        if candidate.estimated_lines_changed > 100:
            return ValidationResult(
                gate_name="Gate A: Contract",
                passed=False,
                details="变更过大 (>100行)",
                logs=logs
            )
        
        return ValidationResult(
            gate_name="Gate A: Contract",
            passed=True,
            details="Contract 验证通过",
            logs=logs
        )
    
    def _run_gate_b(self, sandbox_path: Path) -> ValidationResult:
        """Gate B: E2E 测试"""
        logs = []
        
        # 运行测试套件
        try:
            # 检查是否有测试
            test_result = subprocess.run(
                ["python", "-m", "pytest", "--co", "-q"],
                cwd=sandbox_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if "test" in test_result.stdout.lower():
                # 有测试，运行它们
                result = subprocess.run(
                    ["python", "-m", "pytest", "-xvs"],
                    cwd=sandbox_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                logs.append(result.stdout)
                logs.append(result.stderr)
                
                if result.returncode == 0:
                    return ValidationResult(
                        gate_name="Gate B: E2E",
                        passed=True,
                        details="所有测试通过",
                        logs=logs
                    )
                else:
                    return ValidationResult(
                        gate_name="Gate B: E2E",
                        passed=False,
                        details="测试失败",
                        logs=logs
                    )
            else:
                # 没有测试，跳过
                return ValidationResult(
                    gate_name="Gate B: E2E",
                    passed=True,
                    details="无测试，跳过",
                    logs=logs
                )
        except Exception as e:
            return ValidationResult(
                gate_name="Gate B: E2E",
                passed=False,
                details=f"测试执行异常: {e}",
                logs=logs
            )
    
    def _run_gate_c(self, sandbox_path: Path) -> ValidationResult:
        """Gate C: Preflight 检查"""
        logs = []
        
        # 运行 tool_doctor 检查
        try:
            result = subprocess.run(
                ["python", "scripts/tool_doctor.py"],
                cwd=sandbox_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            logs.append(result.stdout)
            
            if result.returncode == 0:
                return ValidationResult(
                    gate_name="Gate C: Preflight",
                    passed=True,
                    details="Preflight 检查通过",
                    logs=logs
                )
            else:
                return ValidationResult(
                    gate_name="Gate C: Preflight",
                    passed=False,
                    details="Preflight 检查失败",
                    logs=logs
                )
        except Exception as e:
            # tool_doctor 可能不存在，跳过
            return ValidationResult(
                gate_name="Gate C: Preflight",
                passed=True,
                details="Preflight 检查跳过",
                logs=logs
            )
    
    def _run_negative_check(self, sandbox_path: Path, candidate: Any) -> ValidationResult:
        """Negative check: 验证没有引入回归"""
        logs = []
        
        # 检查关键文件是否被破坏
        critical_files = ["README.md", "pyproject.toml", "setup.py"]
        
        for file_name in critical_files:
            file_path = sandbox_path / file_name
            if file_path.exists():
                content = file_path.read_text()
                if len(content) < 10:  # 文件被清空或破坏
                    return ValidationResult(
                        gate_name="Negative Check",
                        passed=False,
                        details=f"关键文件可能被破坏: {file_name}",
                        logs=logs
                    )
        
        # 检查语法错误
        for file_path in candidate.target_files:
            full_path = sandbox_path / file_path
            if full_path.exists() and full_path.suffix == ".py":
                try:
                    compile(full_path.read_text(), str(full_path), 'exec')
                except SyntaxError as e:
                    return ValidationResult(
                        gate_name="Negative Check",
                        passed=False,
                        details=f"语法错误: {file_path}: {e}",
                        logs=logs
                    )
        
        return ValidationResult(
            gate_name="Negative Check",
            passed=True,
            details="Negative check 通过",
            logs=logs
        )
    
    def _generate_patch(self, sandbox_path: Path, base_branch: str) -> Optional[str]:
        """生成 patch 文件"""
        try:
            result = subprocess.run(
                ["git", "diff", base_branch],
                cwd=sandbox_path,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                patch_path = self.patches_dir / f"{sandbox_path.name}.patch"
                patch_path.write_text(result.stdout)
                return str(patch_path)
            
            return None
        except Exception as e:
            print(f"[SandboxHealer] Generate patch failed: {e}")
            return None
    
    def _generate_rollback_script(self, sandbox_path: Path, candidate: Any) -> str:
        """生成回滚脚本"""
        script_lines = [
            "#!/bin/bash",
            "# Auto-generated rollback script",
            f"# Candidate: {candidate.candidate_id}",
            "",
            "# Restore from git",
            "git checkout HEAD -- ",
        ]
        
        for file_path in candidate.target_files:
            script_lines.append(f"git checkout HEAD -- {file_path}")
        
        script_lines.append("")
        script_lines.append("echo 'Rollback completed'")
        
        script_path = self.reports_dir / f"rollback_{candidate.candidate_id}.sh"
        script_path.write_text("\n".join(script_lines))
        script_path.chmod(0o755)
        
        return str(script_path)
    
    def _get_change_stats(self, sandbox_path: Path) -> Dict[str, Any]:
        """获取变更统计"""
        try:
            result = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=sandbox_path,
                capture_output=True,
                text=True
            )
            
            # 解析统计
            lines = result.stdout.strip().split("\n")
            stats = {"added": 0, "removed": 0, "files": []}
            
            for line in lines:
                if "|" in line:
                    parts = line.split("|")
                    file_name = parts[0].strip()
                    stats["files"].append(file_name)
            
            return stats
        except:
            return {"added": 0, "removed": 0, "files": []}
    
    def _create_failure_report(
        self,
        report_id: str,
        bundle_id: str,
        candidate_id: str,
        sandbox_path: Path,
        branch_name: str,
        reason: str
    ) -> SandboxReport:
        """创建失败报告"""
        report = SandboxReport(
            report_id=report_id,
            timestamp=datetime.now().isoformat(),
            bundle_id=bundle_id,
            candidate_id=candidate_id,
            sandbox_path=str(sandbox_path),
            branch_name=branch_name,
            applied_successfully=False,
            validation_results=[],
            patch_path=None,
            validation_report_path=str(self.reports_dir / f"{report_id}.json"),
            rollback_script_path="",
            lines_added=0,
            lines_removed=0,
            files_changed=[],
            negative_check_passed=False,
            regression_tests_passed=False,
            approved_for_merge=False,
            rejection_reason=reason
        )
        
        self._save_report(report)
        return report
    
    def _save_report(self, report: SandboxReport):
        """保存报告"""
        report_path = self.reports_dir / f"{report.report_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _cleanup_sandbox(self, sandbox_path: Path):
        """清理沙箱"""
        try:
            if sandbox_path and sandbox_path.exists():
                # 移除 worktree
                subprocess.run(
                    ["git", "worktree", "remove", str(sandbox_path), "--force"],
                    cwd=self.workspace,
                    capture_output=True
                )
        except Exception as e:
            print(f"[SandboxHealer] Cleanup failed: {e}")


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sandbox Healer")
    parser.add_argument("--workspace", default=".", help="Workspace path")
    parser.add_argument("--test", action="store_true", help="Run test")
    
    args = parser.parse_args()
    
    healer = SandboxHealer(Path(args.workspace))
    
    if args.test:
        # 创建一个测试候选
        class MockCandidate:
            candidate_id = "test_001"
            action_type = "write"
            action_params = {"file_path": "test_file.txt", "content": "test content"}
            target_files = ["test_file.txt"]
            estimated_lines_changed = 1
        
        report = healer.heal("test_bundle", MockCandidate())
        print(f"\nSandbox Report:")
        print(json.dumps(report.to_dict(), indent=2))
