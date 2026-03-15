"""
Telegram Status Bridge - Telegram 状态桥

负责给用户回传状态、进度、审批请求和最终结果。
确保与 task truth 保持一致。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class TaskStatus:
    """任务状态摘要"""
    task_id: str
    status: str
    current_step: Optional[str] = None
    progress: str = ""
    message: str = ""
    can_approve: bool = False
    approval_id: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class StepProgress:
    """步骤进度"""
    step_id: str
    title: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ApprovalRequest:
    """审批请求"""
    approval_id: str
    task_id: str
    step_id: str
    operation_description: str
    risk_level: str
    created_at: str
    expires_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    status: str  # completed, failed, cancelled
    summary: str
    artifacts: List[str] = field(default_factory=list)
    evidence_paths: List[str] = field(default_factory=list)
    completed_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


class TruthLoader:
    """真相加载器 - 从持久化状态加载真实状态"""
    
    def __init__(self, artifacts_dir: str):
        self.artifacts_dir = Path(artifacts_dir)
    
    def load_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """加载任务状态"""
        task_dir = self.artifacts_dir / "tasks" / task_id
        state_file = task_dir / "task_state.json"
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None
    
    def load_gate_report(self, task_id: str) -> Optional[Dict[str, Any]]:
        """加载 Gate 报告"""
        gate_file = self.artifacts_dir / "tasks" / task_id / "final" / "gate_report.json"
        
        if gate_file.exists():
            try:
                with open(gate_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None
    
    def load_summary(self, task_id: str) -> Optional[str]:
        """加载任务摘要"""
        summary_file = self.artifacts_dir / "tasks" / task_id / "final" / "SUMMARY.md"
        
        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    return f.read()
            except IOError:
                return None
        return None


class TelegramStatusBridge:
    """Telegram 状态桥"""
    
    def __init__(self, artifacts_dir: str = "artifacts"):
        self.truth_loader = TruthLoader(artifacts_dir)
    
    def build_status_message(self, task_id: str) -> TaskStatus:
        """
        构建状态消息
        
        从真实状态构建，确保一致性
        """
        task_state = self.truth_loader.load_task_state(task_id)
        
        if not task_state:
            return TaskStatus(
                task_id=task_id,
                status="unknown",
                message="❓ 任务不存在或状态丢失"
            )
        
        # 提取步骤进度
        steps = task_state.get("steps", [])
        completed_steps = sum(1 for s in steps if s.get("status") == "success")
        total_steps = len(steps)
        
        current_step = None
        current_step_status = None
        for step in steps:
            if step.get("status") in ["running", "pending", "failed_retryable", "blocked"]:
                current_step = step.get("step_id")
                current_step_status = step.get("status")
                break
        
        status = task_state.get("status", "unknown")
        
        # 构建状态消息
        status_emoji = {
            "created": "📝",
            "running": "🔄",
            "blocked": "⏸️",
            "completed": "✅",
            "failed": "❌"
        }.get(status, "❓")
        
        message = f"{status_emoji} 任务状态: {status}"
        if current_step:
            message += f"\n📍 当前步骤: {current_step} ({current_step_status})"
        if total_steps > 0:
            message += f"\n📊 进度: {completed_steps}/{total_steps}"
        
        return TaskStatus(
            task_id=task_id,
            status=status,
            current_step=current_step,
            progress=f"{completed_steps}/{total_steps}" if total_steps > 0 else "",
            message=message,
            can_approve=(status == "blocked"),
            created_at=task_state.get("created_at", ""),
            updated_at=task_state.get("updated_at", "")
        )
    
    def build_progress_message(self, task_id: str, step_id: str) -> StepProgress:
        """构建步骤进度消息"""
        task_state = self.truth_loader.load_task_state(task_id)
        
        if not task_state:
            return StepProgress(
                step_id=step_id,
                title="Unknown",
                status="unknown",
                message="任务不存在"
            )
        
        # 查找步骤
        step_info = None
        for step in task_state.get("steps", []):
            if step.get("step_id") == step_id:
                step_info = step
                break
        
        if not step_info:
            return StepProgress(
                step_id=step_id,
                title="Unknown",
                status="not_found",
                message="步骤不存在"
            )
        
        status = step_info.get("status", "unknown")
        status_emoji = {
            "pending": "⏳",
            "running": "🔄",
            "success": "✅",
            "failed_retryable": "🔁",
            "failed_blocked": "⏸️",
            "failed_terminal": "❌"
        }.get(status, "❓")
        
        return StepProgress(
            step_id=step_id,
            title=step_info.get("title", ""),
            status=status,
            started_at=step_info.get("started_at"),
            completed_at=step_info.get("completed_at"),
            message=f"{status_emoji} {step_info.get('title', step_id)}: {status}"
        )
    
    def build_approval_request(
        self,
        approval_id: str,
        task_id: str,
        step_id: str,
        operation_description: str,
        risk_level: str
    ) -> ApprovalRequest:
        """构建审批请求消息"""
        now = datetime.utcnow().isoformat() + "Z"
        
        return ApprovalRequest(
            approval_id=approval_id,
            task_id=task_id,
            step_id=step_id,
            operation_description=operation_description,
            risk_level=risk_level,
            created_at=now
        )
    
    def build_result_message(self, task_id: str) -> TaskResult:
        """构建结果消息"""
        task_state = self.truth_loader.load_task_state(task_id)
        summary = self.truth_loader.load_summary(task_id)
        gate_report = self.truth_loader.load_gate_report(task_id)
        
        if not task_state:
            return TaskResult(
                task_id=task_id,
                status="unknown",
                summary="任务不存在"
            )
        
        status = task_state.get("status", "unknown")
        
        # 提取产物路径
        artifacts = []
        evidence_paths = []
        
        task_dir = self.truth_loader.artifacts_dir / "tasks" / task_id
        if task_dir.exists():
            # 收集产物
            for f in task_dir.rglob("*"):
                if f.is_file():
                    relative = str(f.relative_to(task_dir))
                    if "final" in relative:
                        artifacts.append(relative)
                    elif "evidence" in relative:
                        evidence_paths.append(relative)
        
        # 构建摘要
        result_summary = summary if summary else f"任务 {task_id} 已完成"
        
        # 检查 Gate 结果
        if gate_report:
            all_passed = gate_report.get("all_passed", False)
            if all_passed:
                result_summary = f"✅ {result_summary}"
            else:
                result_summary = f"⚠️ {result_summary}\n\n部分 Gate 检查未通过，请查看详细报告。"
        
        return TaskResult(
            task_id=task_id,
            status=status,
            summary=result_summary,
            artifacts=artifacts[:5],  # 限制数量
            evidence_paths=evidence_paths[:5],
            completed_at=task_state.get("updated_at", "")
        )
    
    def format_status_for_telegram(self, status: TaskStatus) -> str:
        """格式化状态消息为 Telegram 文本"""
        lines = [
            f"📋 **任务状态**",
            f"",
            f"🆔 任务 ID: `{status.task_id}`",
            f"📊 状态: {status.status}",
        ]
        
        if status.current_step:
            lines.append(f"📍 当前步骤: {status.current_step}")
        
        if status.progress:
            lines.append(f"📈 进度: {status.progress}")
        
        if status.can_approve:
            lines.append(f"")
            lines.append(f"⚠️ 此任务正在等待审批")
            lines.append(f"使用 `/approve` 确认或 `/reject` 拒绝")
        
        return "\n".join(lines)
    
    def format_result_for_telegram(self, result: TaskResult) -> str:
        """格式化结果消息为 Telegram 文本"""
        status_emoji = "✅" if result.status == "completed" else "❌"
        
        lines = [
            f"{status_emoji} **任务完成**",
            f"",
            f"🆔 任务 ID: `{result.task_id}`",
            f"📊 最终状态: {result.status}",
            f"",
            f"📝 **摘要**:",
            f"{result.summary}",
        ]
        
        if result.artifacts:
            lines.append(f"")
            lines.append(f"📦 **产物**:")
            for artifact in result.artifacts:
                lines.append(f"  • `{artifact}`")
        
        return "\n".join(lines)
    
    def format_approval_request_for_telegram(self, approval: ApprovalRequest) -> str:
        """格式化审批请求为 Telegram 文本"""
        risk_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴",
            "critical": "🚨"
        }.get(approval.risk_level, "⚠️")
        
        lines = [
            f"🚨 **需要审批**",
            f"",
            f"🆔 任务 ID: `{approval.task_id}`",
            f"📍 步骤: {approval.step_id}",
            f"",
            f"{risk_emoji} 风险等级: **{approval.risk_level}**",
            f"",
            f"📝 **操作**:",
            f"{approval.operation_description}",
            f"",
            f"请确认是否执行此操作。",
            f"",
            f"✅ 使用 `/approve` 确认",
            f"❌ 使用 `/reject` 拒绝",
        ]
        
        return "\n".join(lines)


# 便捷函数
def get_task_status(task_id: str, artifacts_dir: str = "artifacts") -> TaskStatus:
    """便捷函数：获取任务状态"""
    bridge = TelegramStatusBridge(artifacts_dir)
    return bridge.build_status_message(task_id)


def format_status(task_id: str, artifacts_dir: str = "artifacts") -> str:
    """便捷函数：格式化状态消息"""
    bridge = TelegramStatusBridge(artifacts_dir)
    status = bridge.build_status_message(task_id)
    return bridge.format_status_for_telegram(status)
