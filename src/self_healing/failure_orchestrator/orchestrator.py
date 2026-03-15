#!/usr/bin/env python3
"""
Failure Orchestrator - 失败接管中心

职责：
1. 统一接收各类失败事件
2. 生成标准 failure bundle
3. 去重与签名化
4. 路由给后续 planner
"""

import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class FailureType(Enum):
    """失败类型枚举"""
    EDIT_FAILED = "edit_failed"
    TOOL_FAILED = "tool_failed"
    TEST_FAILED = "test_failed"
    BUILD_FAILED = "build_failed"
    RUNTIME_FAILED = "runtime_failed"


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FailureBundle:
    """
    标准失败事件包
    
    包含失败的所有上下文信息，用于后续诊断和修复
    """
    # 标识
    bundle_id: str
    timestamp: str
    
    # 失败信息
    failure_type: str
    tool_name: str
    tool_input: Dict[str, Any]
    stderr: str
    stack_trace: Optional[str]
    
    # 上下文
    related_files: List[str]
    branch: str
    commit: str
    recent_actions: List[Dict]
    
    # 环境
    environment: Dict[str, str]
    
    # 风险与历史
    risk_level: str
    similar_historical_issues: List[str]
    
    # 签名（用于去重和聚类）
    signature: str
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class FailureOrchestrator:
    """失败接管中心"""
    
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.bundles_dir = self.workspace / "artifacts" / "self_healing" / "failure_events"
        self.bundles_dir.mkdir(parents=True, exist_ok=True)
        
        # 已处理 bundle 的缓存（用于去重）
        self._processed_signatures: set = set()
        self._load_processed_signatures()
    
    def _load_processed_signatures(self):
        """加载已处理的签名"""
        for bundle_file in self.bundles_dir.glob("*.json"):
            try:
                with open(bundle_file) as f:
                    data = json.load(f)
                    self._processed_signatures.add(data.get("signature", ""))
            except:
                pass
    
    def _generate_signature(
        self,
        failure_type: str,
        tool_name: str,
        stderr: str,
        related_files: List[str]
    ) -> str:
        """
        生成问题签名
        
        签名用于：
        1. 去重（相同问题不重复处理）
        2. 聚类（相似问题归类）
        3. 历史匹配（查找已知问题）
        """
        # 提取 stderr 的关键行（错误类型、文件路径等）
        key_lines = []
        for line in stderr.split("\n")[:5]:  # 取前5行
            line = line.strip()
            if line and not line.startswith(" "):
                key_lines.append(line)
        
        # 组合签名源
        signature_source = "|".join([
            failure_type,
            tool_name,
            ":".join(sorted(related_files)),
            ":".join(key_lines)
        ])
        
        # 生成哈希
        return hashlib.sha256(signature_source.encode()).hexdigest()[:16]
    
    def _assess_risk(
        self,
        failure_type: str,
        tool_name: str,
        related_files: List[str]
    ) -> RiskLevel:
        """评估风险等级"""
        # 检查是否触及禁区
        critical_files = [
            "SOUL.md", "IDENTITY.md", "SELF_HEALING_CONTRACT.md",
            "subtask-orchestrate", "callback-worker",
            "verify-and-close", "done-guard"
        ]
        
        for file in related_files:
            for critical in critical_files:
                if critical in file:
                    return RiskLevel.CRITICAL
        
        # 根据失败类型评估
        if failure_type == FailureType.EDIT_FAILED.value:
            return RiskLevel.MEDIUM
        elif failure_type == FailureType.TOOL_FAILED.value:
            return RiskLevel.LOW
        elif failure_type == FailureType.RUNTIME_FAILED.value:
            return RiskLevel.HIGH
        
        return RiskLevel.MEDIUM
    
    def _find_similar_issues(self, signature: str) -> List[str]:
        """查找历史相似问题"""
        similar = []
        # TODO: 从 evolution-memory 查询
        return similar
    
    def receive_failure(
        self,
        failure_type: str,
        tool_name: str,
        tool_input: Dict[str, Any],
        stderr: str,
        stack_trace: Optional[str] = None,
        related_files: Optional[List[str]] = None,
        recent_actions: Optional[List[Dict]] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> Optional[FailureBundle]:
        """
        接收失败事件，生成 failure bundle
        
        Args:
            failure_type: 失败类型
            tool_name: 工具名称
            tool_input: 工具输入
            stderr: 标准错误输出
            stack_trace: 堆栈跟踪（可选）
            related_files: 相关文件列表（可选）
            recent_actions: 最近操作轨迹（可选）
            environment: 环境信息（可选）
        
        Returns:
            FailureBundle 或 None（如果已去重）
        """
        related_files = related_files or []
        recent_actions = recent_actions or []
        environment = environment or {}
        
        # 生成签名
        signature = self._generate_signature(
            failure_type, tool_name, stderr, related_files
        )
        
        # 去重检查
        if signature in self._processed_signatures:
            print(f"[FailureOrchestrator] Duplicate signature: {signature}, skipping")
            return None
        
        # 获取 git 信息
        branch = self._get_current_branch()
        commit = self._get_current_commit()
        
        # 评估风险
        risk_level = self._assess_risk(failure_type, tool_name, related_files)
        
        # 查找历史相似问题
        similar_issues = self._find_similar_issues(signature)
        
        # 创建 bundle
        bundle = FailureBundle(
            bundle_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now().isoformat(),
            failure_type=failure_type,
            tool_name=tool_name,
            tool_input=tool_input,
            stderr=stderr,
            stack_trace=stack_trace,
            related_files=related_files,
            branch=branch,
            commit=commit,
            recent_actions=recent_actions,
            environment=environment,
            risk_level=risk_level.value,
            similar_historical_issues=similar_issues,
            signature=signature
        )
        
        # 保存 bundle
        self._save_bundle(bundle)
        
        # 记录已处理
        self._processed_signatures.add(signature)
        
        print(f"[FailureOrchestrator] Created bundle: {bundle.bundle_id} (signature: {signature})")
        
        return bundle
    
    def _get_current_branch(self) -> str:
        """获取当前 git 分支"""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.workspace
            )
            return result.stdout.strip() or "unknown"
        except:
            return "unknown"
    
    def _get_current_commit(self) -> str:
        """获取当前 git commit"""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.workspace
            )
            return result.stdout.strip() or "unknown"
        except:
            return "unknown"
    
    def _save_bundle(self, bundle: FailureBundle):
        """保存 bundle 到文件"""
        filename = f"{bundle.timestamp[:10]}_{bundle.bundle_id}_{bundle.signature}.json"
        filepath = self.bundles_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(bundle.to_json())
    
    def get_pending_bundles(self) -> List[FailureBundle]:
        """获取待处理的 bundles"""
        bundles = []
        
        for bundle_file in sorted(self.bundles_dir.glob("*.json")):
            try:
                with open(bundle_file) as f:
                    data = json.load(f)
                    bundle = FailureBundle(**data)
                    bundles.append(bundle)
            except:
                pass
        
        return bundles
    
    def route_to_planner(self, bundle: FailureBundle) -> bool:
        """
        将 bundle 路由给 remedy planner
        
        Returns:
            True: 成功路由
            False: 路由失败
        """
        # TODO: 调用 remedy planner
        print(f"[FailureOrchestrator] Routing bundle {bundle.bundle_id} to planner")
        return True


# CLI 接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Failure Orchestrator")
    parser.add_argument("--workspace", default=".", help="Workspace path")
    parser.add_argument("--test", action="store_true", help="Run test")
    
    args = parser.parse_args()
    
    orchestrator = FailureOrchestrator(Path(args.workspace))
    
    if args.test:
        # 测试：模拟一个 edit failed
        bundle = orchestrator.receive_failure(
            failure_type="edit_failed",
            tool_name="edit",
            tool_input={
                "file_path": "src/example.py",
                "old_string": "def old_func():",
                "new_string": "def new_func():"
            },
            stderr="Error: old_string not found in file",
            related_files=["src/example.py"],
            recent_actions=[
                {"tool": "read", "file": "src/example.py"},
                {"tool": "edit", "file": "src/example.py", "status": "failed"}
            ]
        )
        
        if bundle:
            print("\nGenerated Bundle:")
            print(bundle.to_json())
