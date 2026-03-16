"""
Resume-Execute Bridge - 恢复到执行的桥接层

将 ResumeEngine 的恢复决策桥接到真实执行器。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from runtime.step_executor import StepExecutor, ExecutionResult
from runtime.resume_engine import ResumeEngine, ResumeContext


class ResumeExecuteBridge:
    """恢复到执行的桥接器"""
    
    def __init__(self, task_dossier, worker_id: str = "bridge_worker"):
        self.dossier = task_dossier
        self.worker_id = worker_id
        self.executor = StepExecutor(task_dossier, worker_id)
        self.resume_engine = ResumeEngine(task_dossier)
    
    def bridge_and_execute(self) -> Dict[str, Any]:
        """分析恢复状态并执行下一步"""
        
        # 1. 分析恢复状态
        context = self.resume_engine.analyze()
        
        # 2. 根据恢复动作决定行为
        action = context.recovery_action
        
        if action == "abort":
            return {
                "executed": False,
                "reason": "recovery_aborted",
                "context": self._context_to_dict(context)
            }
        
        if context.current_step_id is None:
            return {
                "executed": False,
                "reason": "no_current_step",
                "context": self._context_to_dict(context)
            }
        
        step_id = context.current_step_id
        
        # 3. 检查/获取租约
        if not context.lease_valid:
            # 租约无效，尝试获取
            success, lease = self.resume_engine.acquire_lease(step_id, self.worker_id)
            if not success:
                return {
                    "executed": False,
                    "reason": "lease_acquisition_failed",
                    "step_id": step_id,
                    "context": self._context_to_dict(context)
                }
        else:
            # 租约有效，发送心跳
            self.resume_engine.heartbeat(step_id, self.worker_id)
        
        # 4. 加载步骤包
        step_packet = self.dossier.get_step_packet(step_id)
        if step_packet is None:
            return {
                "executed": False,
                "reason": "step_packet_not_found",
                "step_id": step_id
            }
        
        # 5. 执行步骤
        result = self.executor.execute_step(step_packet)
        
        # 6. 收集证据
        evidence = self.executor.collect_evidence(step_packet, result)
        
        # 7. 保存结果
        self.dossier.save_step_result(step_id, result.to_dict())
        
        # 8. 生成 handoff
        handoff = self._generate_handoff(step_packet, result)
        self.dossier.save_handoff(step_id, handoff)
        
        # 9. 更新任务状态
        self.dossier.update_step(step_id, result.status, 
                                  result.error.get("message") if result.error else None)
        
        # 10. 释放租约（如果成功）
        if result.status == "success":
            self.resume_engine.release_lease(step_id, self.worker_id, "step_completed")
        
        return {
            "executed": True,
            "step_id": step_id,
            "status": result.status,
            "result": result.to_dict(),
            "evidence": evidence
        }
    
    def execute_all_pending(self) -> Dict[str, Any]:
        """执行所有待处理步骤直到完成或阻塞"""
        results = []
        
        while True:
            # 分析状态
            context = self.resume_engine.analyze()
            
            # 检查是否完成
            if context.recovery_action == "abort":
                if context.task_state.get("status") == "completed":
                    break
                break
            
            if context.current_step_id is None:
                break
            
            # 执行一步
            step_result = self.bridge_and_execute()
            results.append(step_result)
            
            # 如果执行失败或阻塞，停止
            if not step_result.get("executed"):
                break
            
            if step_result.get("status") not in ("success",):
                break
        
        return {
            "steps_executed": len([r for r in results if r.get("executed")]),
            "results": results,
            "final_status": self._get_final_status()
        }
    
    def _context_to_dict(self, context: ResumeContext) -> Dict[str, Any]:
        """转换上下文为字典"""
        return {
            "task_id": context.task_id,
            "current_step_id": context.current_step_id,
            "current_step_status": context.current_step_status,
            "recovery_action": context.recovery_action,
            "needs_recovery": context.needs_recovery,
            "lease_valid": context.lease_valid
        }
    
    def _generate_handoff(self, step_packet: Dict, result: ExecutionResult) -> str:
        """生成 handoff 文档"""
        step_id = step_packet["step_id"]
        title = step_packet.get("title", step_id)
        goal = step_packet.get("goal", "")
        
        content = f"""# {step_id}: {title}

## Goal
{goal}

## Execution Summary
- **Status**: {result.status}
- **Execution Type**: {result.execution_type}
- **Started**: {result.started_at}
- **Completed**: {result.completed_at}
- **Duration**: {result.duration_ms}ms

"""
        
        if result.command:
            content += f"""## Command
```
{result.command}
```

"""
        
        if result.exit_code is not None:
            content += f"""## Exit Code
{result.exit_code}

"""
        
        if result.outputs:
            content += """## Outputs
```json
%s
```

""" % json.dumps(result.outputs, indent=2)
        
        if result.changed_files:
            content += """## Changed Files
"""
            for f in result.changed_files:
                content += f"- {f['action']}: {f['path']}\n"
            content += "\n"
        
        if result.generated_files:
            content += """## Generated Files
"""
            for f in result.generated_files:
                content += f"- {f}\n"
            content += "\n"
        
        if result.error:
            content += f"""## Error
- **Type**: {result.error.get('type', 'unknown')}
- **Message**: {result.error.get('message', 'N/A')}

"""
        
        content += """## Evidence
- Receipt: `steps/{step_id}/execution_receipt.json`
- Stdout: `evidence/{step_id}/stdout.txt`
- Stderr: `evidence/{step_id}/stderr.txt`
- Timing: `evidence/{step_id}/timing.json`
""".format(step_id=step_id)
        
        return content
    
    def _get_final_status(self) -> str:
        """获取任务最终状态"""
        state = self.dossier.load_state()
        if state is None:
            return "unknown"
        return state.status


def resume_and_execute(task_dossier, worker_id: str = "default") -> Dict[str, Any]:
    """便捷函数：恢复并执行"""
    bridge = ResumeExecuteBridge(task_dossier, worker_id)
    return bridge.bridge_and_execute()
