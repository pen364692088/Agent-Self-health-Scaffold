"""
Step Executor - 真实步骤执行器

执行 step packet 中定义的真实操作，生成 execution receipt 和 evidence。
"""

import json
import os
import subprocess
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
import tempfile


@dataclass
class ExecutionResult:
    """执行结果"""
    step_id: str
    execution_type: str
    status: str  # success, failed, blocked, retryable
    started_at: str
    completed_at: str
    duration_ms: int = 0
    
    # Execution details
    command: Optional[str] = None
    exit_code: Optional[int] = None
    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    
    # File changes
    changed_files: List[Dict[str, Any]] = field(default_factory=list)
    generated_files: List[str] = field(default_factory=list)
    
    # Outputs
    outputs: Dict[str, Any] = field(default_factory=dict)
    
    # Error
    error: Optional[Dict[str, Any]] = None
    retryable: bool = False
    
    # Environment
    environment: Dict[str, str] = field(default_factory=dict)
    
    # Checksum
    checksum: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None or k in ['step_id', 'status']}


class StepExecutor:
    """步骤执行器"""
    
    def __init__(self, task_dossier, worker_id: str = "default_worker"):
        self.dossier = task_dossier
        self.worker_id = worker_id
        self.evidence_dir = task_dossier.evidence_dir
        self.steps_dir = task_dossier.steps_dir
    
    def prepare_execution(self, step_packet: Dict[str, Any], resume_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """准备执行上下文"""
        step_id = step_packet["step_id"]
        
        # 创建证据目录
        evidence_dir = self.evidence_dir / step_id
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查依赖
        missing_deps = []
        for dep in step_packet.get("depends_on", []):
            dep_result_file = self.steps_dir / dep / "result.json"
            if not dep_result_file.exists():
                missing_deps.append(dep)
        
        if missing_deps:
            return {
                "ready": False,
                "reason": "missing_dependencies",
                "missing": missing_deps
            }
        
        # 收集输入文件
        input_files = {}
        for inp in step_packet.get("inputs", []):
            if inp.get("path"):
                path = Path(inp["path"])
                if path.exists():
                    input_files[inp["name"]] = str(path)
        
        return {
            "ready": True,
            "evidence_dir": str(evidence_dir),
            "input_files": input_files,
            "cwd": step_packet.get("execution", {}).get("cwd", os.getcwd())
        }
    
    def execute_step(self, step_packet: Dict[str, Any]) -> ExecutionResult:
        """执行步骤"""
        step_id = step_packet["step_id"]
        step_type = step_packet.get("step_type", "execute_shell")
        
        # 准备执行
        prep = self.prepare_execution(step_packet)
        if not prep.get("ready"):
            return ExecutionResult(
                step_id=step_id,
                execution_type=step_type,
                status="blocked",
                started_at=datetime.utcnow().isoformat() + "Z",
                completed_at=datetime.utcnow().isoformat() + "Z",
                error={"type": "preparation_failed", "message": str(prep)}
            )
        
        # 记录开始时间
        started_at = datetime.utcnow()
        started_at_str = started_at.isoformat() + "Z"
        
        # 创建证据目录
        evidence_dir = self.evidence_dir / step_id
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # 根据类型执行
        try:
            if step_type == "execute_shell":
                result = self._execute_shell(step_packet, evidence_dir, prep)
            elif step_type == "execute_python":
                result = self._execute_python(step_packet, evidence_dir, prep)
            elif step_type == "analyze":
                result = self._execute_analyze(step_packet, evidence_dir, prep)
            elif step_type == "modify_files":
                result = self._execute_modify_files(step_packet, evidence_dir, prep)
            elif step_type == "run_tests":
                result = self._execute_tests(step_packet, evidence_dir, prep)
            elif step_type == "verify_outputs":
                result = self._execute_verify(step_packet, evidence_dir, prep)
            else:
                result = self._execute_shell(step_packet, evidence_dir, prep)
        except Exception as e:
            result = ExecutionResult(
                step_id=step_id,
                execution_type=step_type,
                status="failed",
                started_at=started_at_str,
                completed_at=datetime.utcnow().isoformat() + "Z",
                error={"type": "execution_error", "message": str(e)}
            )
        
        # 计算持续时间
        completed_at = datetime.utcnow()
        result.duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        
        # 计算校验和
        result.checksum = self._calculate_checksum(result)
        
        # 保存 receipt
        self._save_receipt(step_id, result)
        
        return result
    
    def _execute_shell(self, step_packet: Dict, evidence_dir: Path, prep: Dict) -> ExecutionResult:
        """执行 shell 命令"""
        step_id = step_packet["step_id"]
        execution = step_packet.get("execution", {})
        
        command = execution.get("command")
        if not command:
            return ExecutionResult(
                step_id=step_id,
                execution_type="execute_shell",
                status="failed",
                started_at=datetime.utcnow().isoformat() + "Z",
                completed_at=datetime.utcnow().isoformat() + "Z",
                error={"type": "missing_command", "message": "No command specified"}
            )
        
        cwd = execution.get("cwd", prep.get("cwd", os.getcwd()))
        env = execution.get("env", {})
        timeout = execution.get("timeout_seconds", 300)
        
        # 合并环境变量
        full_env = os.environ.copy()
        full_env.update(env)
        
        # 执行命令
        started_at = datetime.utcnow()
        
        try:
            process = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                env=full_env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            exit_code = process.returncode
            stdout = process.stdout
            stderr = process.stderr
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                step_id=step_id,
                execution_type="execute_shell",
                status="failed",
                started_at=started_at.isoformat() + "Z",
                completed_at=datetime.utcnow().isoformat() + "Z",
                command=command,
                exit_code=-1,
                error={"type": "timeout", "message": f"Command timed out after {timeout}s"},
                retryable=True
            )
        except Exception as e:
            return ExecutionResult(
                step_id=step_id,
                execution_type="execute_shell",
                status="failed",
                started_at=started_at.isoformat() + "Z",
                completed_at=datetime.utcnow().isoformat() + "Z",
                command=command,
                error={"type": "execution_error", "message": str(e)},
                retryable=True
            )
        
        # 保存输出
        stdout_path = evidence_dir / "stdout.txt"
        stderr_path = evidence_dir / "stderr.txt"
        exit_code_path = evidence_dir / "exit_code.txt"
        
        stdout_path.write_text(stdout)
        stderr_path.write_text(stderr)
        exit_code_path.write_text(str(exit_code))
        
        # 分类失败
        status = "success" if exit_code == 0 else "failed"
        retryable = False
        error = None
        
        if exit_code != 0:
            failure_type = self._classify_failure(exit_code, stderr)
            if failure_type == "retryable":
                status = "retryable"
                retryable = True
            elif failure_type == "blocked":
                status = "blocked"
            
            error = {
                "type": "command_failed",
                "message": f"Command exited with code {exit_code}",
                "exit_code": exit_code,
                "stderr_snippet": stderr[-500:] if stderr else ""
            }
        
        return ExecutionResult(
            step_id=step_id,
            execution_type="execute_shell",
            status=status,
            started_at=started_at.isoformat() + "Z",
            completed_at=datetime.utcnow().isoformat() + "Z",
            command=command,
            exit_code=exit_code,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            error=error,
            retryable=retryable,
            environment={"cwd": cwd, "hostname": os.uname().nodename}
        )
    
    def _execute_python(self, step_packet: Dict, evidence_dir: Path, prep: Dict) -> ExecutionResult:
        """执行 Python 脚本"""
        step_id = step_packet["step_id"]
        execution = step_packet.get("execution", {})
        
        script = execution.get("script")
        script_path = execution.get("script_path")
        
        if not script and not script_path:
            return ExecutionResult(
                step_id=step_id,
                execution_type="execute_python",
                status="failed",
                started_at=datetime.utcnow().isoformat() + "Z",
                completed_at=datetime.utcnow().isoformat() + "Z",
                error={"type": "missing_script", "message": "No script specified"}
            )
        
        # 如果提供了 script_path，读取脚本内容
        if script_path and not script:
            script = Path(script_path).read_text()
        
        # 执行 Python 脚本
        started_at = datetime.utcnow()
        
        try:
            # 使用 exec 执行脚本
            local_vars = {}
            exec(script, {"__name__": "__main__"}, local_vars)
            
            stdout = ""
            stderr = ""
            exit_code = 0
            
        except Exception as e:
            stdout = ""
            stderr = str(e)
            exit_code = 1
        
        # 保存输出
        stdout_path = evidence_dir / "stdout.txt"
        stderr_path = evidence_dir / "stderr.txt"
        exit_code_path = evidence_dir / "exit_code.txt"
        
        stdout_path.write_text(stdout)
        stderr_path.write_text(stderr)
        exit_code_path.write_text(str(exit_code))
        
        status = "success" if exit_code == 0 else "failed"
        
        return ExecutionResult(
            step_id=step_id,
            execution_type="execute_python",
            status=status,
            started_at=started_at.isoformat() + "Z",
            completed_at=datetime.utcnow().isoformat() + "Z",
            exit_code=exit_code,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            error={"type": "execution_error", "message": stderr} if exit_code != 0 else None
        )
    
    def _execute_analyze(self, step_packet: Dict, evidence_dir: Path, prep: Dict) -> ExecutionResult:
        """执行分析步骤"""
        step_id = step_packet["step_id"]
        execution = step_packet.get("execution", {})
        
        target_path = execution.get("target_path")
        query = execution.get("query", "list")
        
        started_at = datetime.utcnow()
        
        results = {}
        
        if target_path:
            target = Path(target_path)
            if target.exists():
                if target.is_file():
                    results["type"] = "file"
                    results["path"] = str(target)
                    results["size"] = target.stat().st_size
                    results["lines"] = len(target.read_text().splitlines())
                elif target.is_dir():
                    results["type"] = "directory"
                    results["path"] = str(target)
                    results["files"] = [f.name for f in target.iterdir()]
                    results["file_count"] = len(results["files"])
        
        # 保存结果
        result_path = evidence_dir / "analysis_result.json"
        result_path.write_text(json.dumps(results, indent=2))
        
        return ExecutionResult(
            step_id=step_id,
            execution_type="analyze",
            status="success",
            started_at=started_at.isoformat() + "Z",
            completed_at=datetime.utcnow().isoformat() + "Z",
            outputs={"result": results},
            generated_files=[str(result_path)]
        )
    
    def _execute_modify_files(self, step_packet: Dict, evidence_dir: Path, prep: Dict) -> ExecutionResult:
        """执行文件修改"""
        step_id = step_packet["step_id"]
        execution = step_packet.get("execution", {})
        
        operations = execution.get("operations", [])
        
        started_at = datetime.utcnow()
        changed_files = []
        generated_files = []
        
        for op in operations:
            action = op.get("action")
            path = Path(op.get("path"))
            
            if action == "create":
                content = op.get("content", "")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
                changed_files.append({"path": str(path), "action": "created"})
                generated_files.append(str(path))
            
            elif action == "modify":
                if path.exists():
                    content = op.get("content")
                    if content:
                        path.write_text(content)
                        changed_files.append({"path": str(path), "action": "modified"})
            
            elif action == "delete":
                if path.exists():
                    path.unlink()
                    changed_files.append({"path": str(path), "action": "deleted"})
        
        return ExecutionResult(
            step_id=step_id,
            execution_type="modify_files",
            status="success",
            started_at=started_at.isoformat() + "Z",
            completed_at=datetime.utcnow().isoformat() + "Z",
            changed_files=changed_files,
            generated_files=generated_files
        )
    
    def _execute_tests(self, step_packet: Dict, evidence_dir: Path, prep: Dict) -> ExecutionResult:
        """执行测试"""
        step_id = step_packet["step_id"]
        execution = step_packet.get("execution", {})
        
        test_command = execution.get("test_command", "pytest")
        test_path = execution.get("test_path", "")
        
        command = f"{test_command} {test_path}" if test_path else test_command
        
        # 使用 shell 执行测试
        shell_result = self._execute_shell(
            {**step_packet, "execution": {"command": command, **execution}},
            evidence_dir,
            prep
        )
        
        shell_result.execution_type = "run_tests"
        
        # 解析测试结果
        if shell_result.status == "success":
            stdout_path = evidence_dir / "stdout.txt"
            if stdout_path.exists():
                stdout = stdout_path.read_text()
                # 简单解析 pytest 输出
                import re
                passed_match = re.search(r"(\d+) passed", stdout)
                failed_match = re.search(r"(\d+) failed", stdout)
                
                shell_result.outputs = {
                    "tests_passed": int(passed_match.group(1)) if passed_match else 0,
                    "tests_failed": int(failed_match.group(1)) if failed_match else 0
                }
        
        return shell_result
    
    def _execute_verify(self, step_packet: Dict, evidence_dir: Path, prep: Dict) -> ExecutionResult:
        """执行验证"""
        step_id = step_packet["step_id"]
        execution = step_packet.get("execution", {})
        
        expected_files = execution.get("expected_files", [])
        validators = execution.get("validators", [])
        
        started_at = datetime.utcnow()
        results = {
            "files_checked": [],
            "validations": [],
            "all_passed": True
        }
        
        # 检查文件存在
        for file_path in expected_files:
            exists = Path(file_path).exists()
            results["files_checked"].append({
                "path": file_path,
                "exists": exists
            })
            if not exists:
                results["all_passed"] = False
        
        status = "success" if results["all_passed"] else "failed"
        
        return ExecutionResult(
            step_id=step_id,
            execution_type="verify_outputs",
            status=status,
            started_at=started_at.isoformat() + "Z",
            completed_at=datetime.utcnow().isoformat() + "Z",
            outputs=results
        )
    
    def collect_evidence(self, step_packet: Dict, result: ExecutionResult) -> Dict[str, Any]:
        """收集执行证据"""
        step_id = step_packet["step_id"]
        evidence_dir = self.evidence_dir / step_id
        
        evidence = {
            "receipt_path": str(self.steps_dir / step_id / "execution_receipt.json"),
            "stdout_path": result.stdout_path,
            "stderr_path": result.stderr_path,
            "timing": {
                "started_at": result.started_at,
                "completed_at": result.completed_at,
                "duration_ms": result.duration_ms
            }
        }
        
        # 保存 timing.json
        timing_path = evidence_dir / "timing.json"
        timing_path.write_text(json.dumps(evidence["timing"], indent=2))
        
        return evidence
    
    def _classify_failure(self, exit_code: int, stderr: str) -> str:
        """分类失败类型"""
        if exit_code in [137, 143]:  # SIGKILL, SIGTERM
            return "retryable"
        if exit_code == 126:  # Permission denied
            return "blocked"
        if exit_code == 127:  # Command not found
            return "fatal"
        
        stderr_lower = stderr.lower()
        if "permission denied" in stderr_lower:
            return "blocked"
        if "not found" in stderr_lower:
            return "fatal"
        if "timeout" in stderr_lower:
            return "retryable"
        if "connection" in stderr_lower or "network" in stderr_lower:
            return "retryable"
        
        # Default: generic command failure
        return "failed"
    
    def _calculate_checksum(self, result: ExecutionResult) -> str:
        """计算结果校验和"""
        data = result.to_dict()
        data.pop("checksum", None)
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def _save_receipt(self, step_id: str, result: ExecutionResult) -> None:
        """保存执行收据"""
        receipt_path = self.steps_dir / step_id / "execution_receipt.json"
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(receipt_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)


def execute_step(dossier, step_packet: Dict[str, Any], worker_id: str = "default") -> ExecutionResult:
    """便捷函数：执行步骤"""
    executor = StepExecutor(dossier, worker_id)
    return executor.execute_step(step_packet)
