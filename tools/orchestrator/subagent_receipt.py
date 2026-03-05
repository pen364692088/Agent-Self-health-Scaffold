#!/usr/bin/env python3
"""
Subagent Receipt Handler v2.0
Provides utilities for subagents to send completion receipts

Standard Receipt Schema:
{
  "task_id": str,
  "run_id": str,
  "session_key": str,
  "status": "ok|fail|timeout",
  "summary": str,
  "artifacts": [str],
  "error": {"type": str, "message": str, "trace": str} | null,
  "ts": "ISO8601 timestamp"
}
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class SubagentReceiptHandler:
    """Handler for subagents to send completion receipts"""
    
    def __init__(self, workspace_dir: str = "/home/moonlight/.openclaw/workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.subtasks_dir = self.workspace_dir / "reports" / "subtasks"
        self.subtasks_dir.mkdir(parents=True, exist_ok=True)
    
    def send_receipt(
        self,
        task_id: str,
        run_id: str,
        status: str = "ok",
        summary: str = "",
        session_key: str = "",
        artifacts: List[str] = None,
        error: Dict[str, Any] = None,
        **kwargs
    ) -> bool:
        """
        Send a completion receipt for a subtask.
        
        Args:
            task_id: Unique task identifier
            run_id: Run ID from spawn response
            status: "ok" or "fail" or "timeout"
            summary: Brief summary of what was done
            session_key: Session key (optional)
            artifacts: List of output file paths
            error: Error dict with type/message/trace (if failed)
            **kwargs: Additional metadata (will be added to receipt)
            
        Returns:
            True if receipt was written successfully
        """
        # Validate status
        if status not in ['ok', 'fail', 'timeout']:
            status = 'fail'
        
        receipt = {
            "task_id": task_id,
            "run_id": run_id,
            "session_key": session_key,
            "status": status,
            "summary": summary,
            "artifacts": artifacts or [],
            "error": error,
            "ts": datetime.now().isoformat(),
            # Include any extra metadata
            "metadata": kwargs
        }
        
        receipt_file = self.subtasks_dir / f"{task_id}.done.json"
        
        try:
            with open(receipt_file, 'w') as f:
                json.dump(receipt, f, indent=2)
            return True
        except Exception as e:
            print(f"Error writing receipt: {e}")
            return False
    
    def send_done_receipt(
        self,
        task_id: str,
        run_id: str,
        summary: str,
        session_key: str = "",
        artifacts: List[str] = None,
        **kwargs
    ) -> bool:
        """
        Send a success receipt for a subtask.
        
        Args:
            task_id: Unique task identifier
            run_id: Run ID from spawn response
            summary: Brief summary of what was done
            session_key: Session key (optional)
            artifacts: List of output file paths
            **kwargs: Additional metadata
            
        Returns:
            True if receipt was written successfully
        """
        return self.send_receipt(
            task_id=task_id,
            run_id=run_id,
            status="ok",
            summary=summary,
            session_key=session_key,
            artifacts=artifacts,
            **kwargs
        )
    
    def send_fail_receipt(
        self,
        task_id: str,
        run_id: str,
        error: str,
        error_type: str = "error",
        error_trace: str = None,
        session_key: str = "",
        artifacts: List[str] = None,
        **kwargs
    ) -> bool:
        """
        Send a failure receipt for a subtask.
        
        Args:
            task_id: Unique task identifier
            run_id: Run ID from spawn response
            error: Error message describing the failure
            error_type: Type of error (default: "error")
            error_trace: Stack trace (optional)
            session_key: Session key (optional)
            artifacts: List of any partial output files
            **kwargs: Additional metadata
            
        Returns:
            True if receipt was written successfully
        """
        error_dict = {
            "type": error_type,
            "message": error,
            "trace": error_trace
        }
        
        return self.send_receipt(
            task_id=task_id,
            run_id=run_id,
            status="fail",
            summary=f"FAILED: {error}",
            session_key=session_key,
            artifacts=artifacts,
            error=error_dict,
            **kwargs
        )
    
    def send_timeout_receipt(
        self,
        task_id: str,
        run_id: str,
        summary: str = "Task timed out",
        session_key: str = "",
        **kwargs
    ) -> bool:
        """
        Send a timeout receipt for a subtask.
        """
        return self.send_receipt(
            task_id=task_id,
            run_id=run_id,
            status="timeout",
            summary=summary,
            session_key=session_key,
            **kwargs
        )


# Convenience functions for subagents

def subtask_done(
    task_id: str,
    run_id: str,
    summary: str,
    session_key: str = "",
    artifacts: List[str] = None,
    **kwargs
) -> bool:
    """
    Convenience function for subagents to signal completion.
    
    Usage in subagent:
        from subagent_receipt import subtask_done
        
        # ... do work ...
        
        subtask_done(
            task_id="task_abc123",
            run_id="run_xyz",
            summary="Completed document analysis",
            artifacts=["/path/to/output.json"]
        )
    """
    handler = SubagentReceiptHandler()
    return handler.send_done_receipt(
        task_id=task_id,
        run_id=run_id,
        summary=summary,
        session_key=session_key,
        artifacts=artifacts,
        **kwargs
    )


def subtask_fail(
    task_id: str,
    run_id: str,
    error: str,
    error_type: str = "error",
    session_key: str = "",
    artifacts: List[str] = None,
    **kwargs
) -> bool:
    """
    Convenience function for subagents to signal failure.
    """
    handler = SubagentReceiptHandler()
    return handler.send_fail_receipt(
        task_id=task_id,
        run_id=run_id,
        error=error,
        error_type=error_type,
        session_key=session_key,
        artifacts=artifacts,
        **kwargs
    )


def subtask_timeout(
    task_id: str,
    run_id: str,
    summary: str = "Task timed out",
    session_key: str = "",
    **kwargs
) -> bool:
    """
    Convenience function for subagents to signal timeout.
    """
    handler = SubagentReceiptHandler()
    return handler.send_timeout_receipt(
        task_id=task_id,
        run_id=run_id,
        summary=summary,
        session_key=session_key,
        **kwargs
    )


if __name__ == "__main__":
    # Test the receipt handler
    print("Testing receipt handler...")
    
    handler = SubagentReceiptHandler()
    
    # Test success receipt
    result = handler.send_done_receipt(
        task_id="test_task_001",
        run_id="test_run_001",
        summary="Test completion",
        artifacts=["/tmp/test.json"]
    )
    print(f"Success receipt: {result}")
    
    # Test fail receipt
    result = handler.send_fail_receipt(
        task_id="test_task_002",
        run_id="test_run_002",
        error="Something went wrong",
        error_type="runtime_error"
    )
    print(f"Fail receipt: {result}")
    
    # Verify files
    print("\nReceipt files:")
    for f in handler.subtasks_dir.glob("*.done.json"):
        with open(f) as fp:
            data = json.load(fp)
            print(f"  {f.name}: status={data['status']}")
