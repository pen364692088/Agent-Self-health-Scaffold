"""
Step Packet Compiler - 步骤执行包编译器

将高层计划转换为可独立执行的步骤包。
每个步骤包必须是自包含的，可以在上下文丢失后独立恢复执行。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict


class StepPacketCompiler:
    """步骤执行包编译器"""
    
    def __init__(self, schema_dir: Optional[str] = None):
        self.schema_dir = schema_dir
    
    def compile_plan(self, plan: List[Dict[str, Any]], task_id: str, artifacts_dir: str) -> List[Dict[str, Any]]:
        """将计划编译为步骤执行包列表"""
        packets = []
        
        for i, step in enumerate(plan):
            packet = self._compile_step(step, i + 1, task_id, artifacts_dir, plan)
            packets.append(packet)
        
        return packets
    
    def _compile_step(self, step: Dict[str, Any], index: int, task_id: str, artifacts_dir: str, full_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """编译单个步骤包"""
        step_id = step.get("step_id", f"S{index:02d}")
        
        # 构建输入依赖
        inputs = self._build_inputs(step, full_plan, artifacts_dir)
        
        # 构建允许文件列表
        allowed_files = self._build_allowed_files(step)
        
        # 构建预期输出
        expected_outputs = self._build_expected_outputs(step, step_id, artifacts_dir)
        
        # 构建退出标准
        exit_criteria = self._build_exit_criteria(step, expected_outputs)
        
        # 构建失败策略
        failure_policy = self._build_failure_policy(step)
        
        packet = {
            "step_id": step_id,
            "version": "v1.0",
            "title": step.get("title", step.get("goal", f"Step {index}")),
            "goal": step.get("goal", step.get("description", "Execute step")),
            "description": step.get("description", ""),
            "inputs": inputs,
            "allowed_files": allowed_files,
            "expected_outputs": expected_outputs,
            "exit_criteria": exit_criteria,
            "failure_policy": failure_policy,
            "depends_on": step.get("depends_on", []),
            "timeout_seconds": step.get("timeout_seconds", 300),
            "checkpoint_before": step.get("checkpoint_before", True),
            "metadata": {
                "task_id": task_id,
                "compiled_at": datetime.utcnow().isoformat() + "Z",
                "source": step
            }
        }
        
        return packet
    
    def _build_inputs(self, step: Dict[str, Any], full_plan: List[Dict[str, Any]], artifacts_dir: str) -> List[Dict[str, Any]]:
        """构建输入依赖"""
        inputs = []
        
        # 从步骤定义获取输入
        for inp in step.get("inputs", []):
            inputs.append({
                "name": inp.get("name"),
                "path": inp.get("path"),
                "type": inp.get("type", "file"),
                "required": inp.get("required", True),
                "from_step": inp.get("from_step")
            })
        
        # 从依赖步骤推导输入
        for dep_id in step.get("depends_on", []):
            # 查找依赖步骤的输出
            dep_step = self._find_step(full_plan, dep_id)
            if dep_step:
                for out in dep_step.get("outputs", []):
                    inputs.append({
                        "name": f"{dep_id}_{out.get('name', 'output')}",
                        "path": f"{artifacts_dir}/evidence/{dep_id}/{out.get('path', '')}",
                        "type": "file",
                        "required": True,
                        "from_step": dep_id
                    })
        
        return inputs
    
    def _find_step(self, plan: List[Dict[str, Any]], step_id: str) -> Optional[Dict[str, Any]]:
        """在计划中查找步骤"""
        for step in plan:
            if step.get("step_id", step.get("id")) == step_id:
                return step
        return None
    
    def _build_allowed_files(self, step: Dict[str, Any]) -> List[str]:
        """构建允许修改的文件列表"""
        allowed = step.get("allowed_files", [])
        
        # 如果没有指定，允许所有文件（但建议明确指定）
        if not allowed and not step.get("restrict_files", False):
            allowed = ["*"]  # 通配符表示允许所有
        
        return allowed
    
    def _build_expected_outputs(self, step: Dict[str, Any], step_id: str, artifacts_dir: str) -> List[Dict[str, Any]]:
        """构建预期输出"""
        outputs = []
        
        for out in step.get("outputs", []):
            outputs.append({
                "name": out.get("name"),
                "path": out.get("path", f"{artifacts_dir}/evidence/{step_id}/{out.get('name', 'output')}"),
                "type": out.get("type", "file"),
                "validator": out.get("validator"),
                "required": out.get("required", True)
            })
        
        # 默认输出：result.json 和 handoff
        if not any(o.get("name") == "result" for o in outputs):
            outputs.append({
                "name": "result",
                "path": f"{artifacts_dir}/steps/{step_id}/result.json",
                "type": "file",
                "validator": "json_schema:step_result.schema.json",
                "required": True
            })
        
        return outputs
    
    def _build_exit_criteria(self, step: Dict[str, Any], expected_outputs: List[Dict[str, Any]]) -> List[str]:
        """构建退出标准"""
        criteria = step.get("exit_criteria", [])
        
        # 自动添加输出存在性检查
        for out in expected_outputs:
            if out.get("required", True):
                criteria.append(f"Output '{out['name']}' exists at {out['path']}")
        
        # 添加测试通过检查（如果有）
        if step.get("run_tests", False):
            criteria.append("All tests pass")
        
        return criteria
    
    def _build_failure_policy(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """构建失败策略"""
        default_policy = {
            "max_retries": 3,
            "backoff": "exponential",
            "backoff_base_ms": 1000,
            "on_failure": "block",
            "notify_on": ["blocked", "failed"]
        }
        
        policy = step.get("failure_policy", {})
        return {**default_policy, **policy}
    
    def save_packets(self, packets: List[Dict[str, Any]], task_dossier) -> None:
        """保存步骤包到任务档案"""
        for packet in packets:
            task_dossier.save_step_packet(packet["step_id"], packet)
    
    def validate_packet(self, packet: Dict[str, Any]) -> List[str]:
        """验证步骤包完整性"""
        errors = []
        
        # 检查必需字段
        required_fields = ["step_id", "title", "goal", "inputs", "exit_criteria", "failure_policy"]
        for field in required_fields:
            if field not in packet:
                errors.append(f"Missing required field: {field}")
        
        # 检查步骤 ID 格式
        if "step_id" in packet:
            import re
            if not re.match(r"^S[0-9]+$", packet["step_id"]):
                errors.append(f"Invalid step_id format: {packet['step_id']}")
        
        # 检查输入有效性
        for inp in packet.get("inputs", []):
            if not inp.get("name"):
                errors.append("Input missing name")
        
        # 检查退出标准
        if not packet.get("exit_criteria"):
            errors.append("No exit criteria defined")
        
        return errors


def compile_task_plan(task_id: str, plan: List[Dict[str, Any]], artifacts_dir: str) -> List[Dict[str, Any]]:
    """便捷函数：编译任务计划"""
    compiler = StepPacketCompiler()
    return compiler.compile_plan(plan, task_id, artifacts_dir)
