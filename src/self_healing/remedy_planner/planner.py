#!/usr/bin/env python3
"""
Remedy Planner - 候选修复方案生成器

职责：
1. 根据问题签名生成候选修复方案
2. 检索历史成功案例
3. 生成 3-5 个候选方案
4. 输出方案池给评分器
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum


class RemedySource(Enum):
    """修复方案来源"""
    HISTORICAL = "historical"       # 历史成功案例
    TEMPLATE = "template"           # 模板修复
    MINIMAL_CHANGE = "minimal"      # 最小变更
    ROLLBACK_REPLAY = "rollback"    # 回退重放
    EXTERNAL_PATTERN = "external"   # 外部模式
    MANUAL_ESCALATION = "manual"    # 升级人工


@dataclass
class RemedyCandidate:
    """候选修复方案"""
    # 标识
    candidate_id: str
    source: str
    
    # 方案内容
    name: str
    description: str
    action_type: str              # edit, exec, config, etc.
    action_params: Dict[str, Any] # 动作参数
    
    # 影响范围
    target_files: List[str]
    estimated_lines_changed: int
    
    # 验证信息
    preconditions: List[str]      # 前置条件
    expected_outcome: str         # 预期结果
    rollback_steps: List[str]     # 回滚步骤
    
    # 元数据
    historical_success_rate: float
    similar_cases: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class RemedyPlanner:
    """修复方案规划器"""
    
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.templates_dir = self.workspace / "src" / "self_healing" / "remedy_planner" / "templates"
        self.history_db = self.workspace / "memory" / "successful_remedies.jsonl"
        self.external_patterns = self.workspace / "src" / "self_healing" / "shadow_planner" / "patterns"
        
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载内置模板
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """加载内置修复模板"""
        self.builtin_templates = {
            "edit_failed_target_missing": {
                "name": "重新读取后重试 edit",
                "description": "文件内容可能已变化，重新读取后再次尝试 edit",
                "action_type": "compound",
                "action_params": {
                    "steps": [
                        {"tool": "read", "file_path": "{target_file}"},
                        {"tool": "edit", "file_path": "{target_file}", "old_string": "{fresh_old_string}", "new_string": "{new_string}"}
                    ]
                },
                "applicable_signatures": ["edit_failed+target_missing"],
            },
            "tool_failed_permission_denied": {
                "name": "检查权限并申请提升",
                "description": "权限不足，检查文件权限并申请 sudo 或修改权限",
                "action_type": "compound",
                "action_params": {
                    "steps": [
                        {"tool": "exec", "command": "ls -la {target_file}"},
                        {"tool": "exec", "command": "sudo chmod +w {target_file} || echo 'Need manual permission'"}
                    ]
                },
                "applicable_signatures": ["tool_failed+permission_denied"],
            },
            "file_not_found_create": {
                "name": "创建缺失文件",
                "description": "文件不存在，创建新文件",
                "action_type": "write",
                "action_params": {
                    "file_path": "{target_file}",
                    "content": "{default_content}"
                },
                "applicable_signatures": ["file_not_found"],
            },
            "dependency_missing_install": {
                "name": "安装缺失依赖",
                "description": "使用包管理器安装缺失的依赖",
                "action_type": "exec",
                "action_params": {
                    "command": "pip install {package_name} || npm install {package_name}"
                },
                "applicable_signatures": ["dependency_build"],
            },
            "rollback_to_last_known_good": {
                "name": "回退到最近稳定点",
                "description": "回退到最近的稳定 commit，然后重放必要操作",
                "action_type": "compound",
                "action_params": {
                    "steps": [
                        {"tool": "exec", "command": "git stash"},
                        {"tool": "exec", "command": "git checkout {last_good_commit}"},
                        {"tool": "exec", "command": "git stash pop"}
                    ]
                },
                "applicable_signatures": ["*"],  # 通用
            },
        }
    
    def plan_remedies(
        self,
        signature: str,
        failure_type: str,
        root_cause: str,
        context_hint: str,
        related_files: List[str],
        stderr: str
    ) -> List[RemedyCandidate]:
        """
        生成候选修复方案
        
        策略优先级：
        1. 最小变更修复
        2. 最近稳定点回退并重放
        3. 历史模板修复
        4. 外部模式参考修复
        5. 升级人工/冻结主链
        
        Returns:
            3-5 个候选方案，按推荐度排序
        """
        candidates = []
        
        # 1. 最小变更修复（最高优先级）
        minimal_candidate = self._generate_minimal_fix(
            signature, failure_type, root_cause, related_files, stderr
        )
        if minimal_candidate:
            candidates.append(minimal_candidate)
        
        # 2. 回退重放
        rollback_candidate = self._generate_rollback_replay(
            signature, related_files
        )
        if rollback_candidate:
            candidates.append(rollback_candidate)
        
        # 3. 历史模板修复
        historical_candidates = self._generate_from_history(
            signature, failure_type, root_cause
        )
        candidates.extend(historical_candidates[:2])  # 最多2个历史方案
        
        # 4. 外部模式参考
        external_candidates = self._generate_from_external_patterns(
            signature, failure_type, root_cause
        )
        candidates.extend(external_candidates[:1])  # 最多1个外部方案
        
        # 5. 升级人工（保底方案）
        manual_candidate = self._generate_manual_escalation(
            signature, failure_type, stderr
        )
        candidates.append(manual_candidate)
        
        # 确保至少3个，最多5个
        while len(candidates) < 3:
            # 添加通用回退方案
            candidates.append(self._generate_generic_fallback(signature))
        
        return candidates[:5]
    
    def _generate_minimal_fix(
        self,
        signature: str,
        failure_type: str,
        root_cause: str,
        related_files: List[str],
        stderr: str
    ) -> Optional[RemedyCandidate]:
        """生成最小变更修复方案"""
        
        # 根据根因选择最小修复
        if root_cause == "target_missing":
            return RemedyCandidate(
                candidate_id=f"minimal_{hash(signature) % 10000}",
                source=RemedySource.MINIMAL_CHANGE.value,
                name="重新读取目标文件后重试",
                description="文件内容可能已变化，重新读取获取最新内容后再次尝试 edit",
                action_type="compound",
                action_params={
                    "steps": [
                        {"tool": "read", "file_path": related_files[0] if related_files else "unknown"},
                        {"tool": "edit", "file_path": related_files[0] if related_files else "unknown", "note": "使用重新读取的内容"}
                    ]
                },
                target_files=related_files[:1],
                estimated_lines_changed=1,
                preconditions=["文件可读", "有写入权限"],
                expected_outcome="edit 成功应用",
                rollback_steps=["git checkout {file}"],
                historical_success_rate=0.85,
                similar_cases=[]
            )
        
        elif root_cause == "permission_denied":
            return RemedyCandidate(
                candidate_id=f"minimal_{hash(signature) % 10000}",
                source=RemedySource.MINIMAL_CHANGE.value,
                name="修改文件权限",
                description="使用 chmod 修改文件权限",
                action_type="exec",
                action_params={
                    "command": f"chmod +w {related_files[0] if related_files else '$FILE'}"
                },
                target_files=related_files[:1],
                estimated_lines_changed=0,
                preconditions=["有权限修改权限", "不是系统文件"],
                expected_outcome="权限修改成功，可以写入",
                rollback_steps=["chmod -w {file}"],
                historical_success_rate=0.90,
                similar_cases=[]
            )
        
        elif root_cause == "PATH_missing":
            return RemedyCandidate(
                candidate_id=f"minimal_{hash(signature) % 10000}",
                source=RemedySource.MINIMAL_CHANGE.value,
                name="使用完整路径或安装依赖",
                description="使用完整路径执行命令，或安装缺失的包",
                action_type="exec",
                action_params={
                    "command": "which {command} || (apt-get install {package} || pip install {package})"
                },
                target_files=[],
                estimated_lines_changed=0,
                preconditions=["有安装权限"],
                expected_outcome="命令可用",
                rollback_steps=[],
                historical_success_rate=0.75,
                similar_cases=[]
            )
        
        return None
    
    def _generate_rollback_replay(
        self,
        signature: str,
        related_files: List[str]
    ) -> Optional[RemedyCandidate]:
        """生成回退重放方案"""
        return RemedyCandidate(
            candidate_id=f"rollback_{hash(signature) % 10000}",
            source=RemedySource.ROLLBACK_REPLAY.value,
            name="回退到最近稳定 commit 并重放",
            description="保存当前更改，回退到最近的稳定点，然后重新应用更改",
            action_type="compound",
            action_params={
                "steps": [
                    {"tool": "exec", "command": "git stash push -m 'auto-remedy-stash'"},
                    {"tool": "exec", "command": "git log --oneline -10 --grep='PASS' | head -1 | cut -d' ' -f1", "capture": "last_good_commit"},
                    {"tool": "exec", "command": "git checkout {last_good_commit}"},
                    {"tool": "exec", "command": "git stash pop"}
                ]
            },
            target_files=related_files,
            estimated_lines_changed=len(related_files),
            preconditions=["git 可用", "有历史 commit", "无未推送的重要更改"],
            expected_outcome="回到稳定状态并保留当前更改",
            rollback_steps=["git checkout main", "git stash pop"],
            historical_success_rate=0.70,
            similar_cases=[]
        )
    
    def _generate_from_history(
        self,
        signature: str,
        failure_type: str,
        root_cause: str
    ) -> List[RemedyCandidate]:
        """从历史成功案例生成方案"""
        candidates = []
        
        if not self.history_db.exists():
            return candidates
        
        try:
            with open(self.history_db) as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        # 匹配签名前缀
                        if record.get("signature", "").startswith(signature[:8]):
                            candidate = RemedyCandidate(
                                candidate_id=f"hist_{record.get('id', 'unknown')}",
                                source=RemedySource.HISTORICAL.value,
                                name=record.get("remedy_name", "历史成功方案"),
                                description=record.get("description", ""),
                                action_type=record.get("action_type", "unknown"),
                                action_params=record.get("action_params", {}),
                                target_files=record.get("target_files", []),
                                estimated_lines_changed=record.get("lines_changed", 1),
                                preconditions=record.get("preconditions", []),
                                expected_outcome=record.get("expected_outcome", ""),
                                rollback_steps=record.get("rollback_steps", []),
                                historical_success_rate=record.get("success_rate", 0.8),
                                similar_cases=[record.get("signature", "")]
                            )
                            candidates.append(candidate)
                    except:
                        pass
        except:
            pass
        
        return candidates
    
    def _generate_from_external_patterns(
        self,
        signature: str,
        failure_type: str,
        root_cause: str
    ) -> List[RemedyCandidate]:
        """从外部模式生成方案（影子层）"""
        candidates = []
        
        # 检查外部模式目录
        if not self.external_patterns.exists():
            return candidates
        
        # TODO: 从 shadow planner 加载外部模式
        # 当前返回空，外部模式需要经过观察窗口才能使用
        
        return candidates
    
    def _generate_manual_escalation(
        self,
        signature: str,
        failure_type: str,
        stderr: str
    ) -> RemedyCandidate:
        """生成人工升级方案（保底）"""
        return RemedyCandidate(
            candidate_id=f"manual_{hash(signature) % 10000}",
            source=RemedySource.MANUAL_ESCALATION.value,
            name="升级人工处理",
            description=f"自动修复无法安全处理此问题，需要人工审查。失败类型: {failure_type}",
            action_type="notify",
            action_params={
                "channel": "user",
                "message": f"需要人工处理的问题\n签名: {signature}\n错误: {stderr[:200]}"
            },
            target_files=[],
            estimated_lines_changed=0,
            preconditions=["人工可用"],
            expected_outcome="人工介入处理",
            rollback_steps=[],
            historical_success_rate=1.0,  # 人工处理成功率视为100%
            similar_cases=[]
        )
    
    def _generate_generic_fallback(self, signature: str) -> RemedyCandidate:
        """生成通用回退方案"""
        return RemedyCandidate(
            candidate_id=f"fallback_{hash(signature) % 10000}",
            source=RemedySource.TEMPLATE.value,
            name="通用重试",
            description="等待后重试操作",
            action_type="wait",
            action_params={"seconds": 5},
            target_files=[],
            estimated_lines_changed=0,
            preconditions=["无"],
            expected_outcome="临时问题可能已解决",
            rollback_steps=[],
            historical_success_rate=0.3,
            similar_cases=[]
        )


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remedy Planner")
    parser.add_argument("--workspace", default=".", help="Workspace path")
    parser.add_argument("--test", action="store_true", help="Run test")
    
    args = parser.parse_args()
    
    planner = RemedyPlanner(Path(args.workspace))
    
    if args.test:
        # 测试
        candidates = planner.plan_remedies(
            signature="edit_failed+target_missing+none",
            failure_type="edit_failed",
            root_cause="target_missing",
            context_hint="none",
            related_files=["src/example.py"],
            stderr="Error: old_string not found"
        )
        
        print(f"\nGenerated {len(candidates)} candidates:")
        for i, c in enumerate(candidates, 1):
            print(f"\n{i}. {c.name} ({c.source})")
            print(f"   {c.description}")
            print(f"   Success rate: {c.historical_success_rate}")
