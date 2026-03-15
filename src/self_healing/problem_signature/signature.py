#!/usr/bin/env python3
"""
Problem Signature - 问题签名系统

职责：
1. L1 故障分类（高层类别）
2. L2 根因签名（精确指纹）
3. 签名匹配与聚类
4. 历史问题关联
"""

import re
import json
import hashlib
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path


class L1Category(Enum):
    """L1 故障分类 - 高层类别"""
    PERMISSION_PATH = "permission_path"           # 权限/路径
    FILE_NOT_FOUND = "file_not_found"             # 文件不存在
    EDIT_CONTRACT_VIOLATION = "edit_contract"     # edit 契约不满足
    CONTEXT_MISSING = "context_missing"           # 上下文缺失
    DEPENDENCY_BUILD = "dependency_build"         # 依赖/构建异常
    CONCURRENCY_ORDER = "concurrency_order"       # 并发/消息顺序冲突
    TEST_ASSERTION = "test_assertion"             # 测试断言失败
    FRAMEWORK_CONTRACT = "framework_contract"     # 框架契约变化
    HALLUCINATION = "hallucination"               # 幻觉性修改
    UNKNOWN = "unknown"                           # 未知


@dataclass
class L2Signature:
    """L2 根因签名 - 精确指纹"""
    # 基础组件
    failure_type: str           # edit_failed, tool_failed, etc.
    root_cause: str             # target_missing, permission_denied, etc.
    context_hint: str           # branch_dirty, PATH_missing, etc.
    
    # 生成的签名
    signature: str              # 完整签名字符串
    signature_hash: str         # 签名哈希（用于匹配）
    
    # 元数据
    confidence: float           # 置信度 0-1
    matching_rules: List[str]   # 匹配到的规则
    
    def to_dict(self) -> Dict:
        return {
            "failure_type": self.failure_type,
            "root_cause": self.root_cause,
            "context_hint": self.context_hint,
            "signature": self.signature,
            "signature_hash": self.signature_hash,
            "confidence": self.confidence,
            "matching_rules": self.matching_rules
        }


class SignatureMatcher:
    """签名匹配器 - 从失败信息中提取签名"""
    
    # L1 分类规则
    L1_RULES = {
        L1Category.PERMISSION_PATH: [
            r"permission denied",
            r"PermissionError",
            r"EACCES",
            r"access denied",
            r"not permitted",
        ],
        L1Category.FILE_NOT_FOUND: [
            r"No such file",
            r"FileNotFoundError",
            r"ENOENT",
            r"does not exist",
            r"not found",
        ],
        L1Category.EDIT_CONTRACT_VIOLATION: [
            r"old_string not found",
            r"does not contain",
            r"edit failed",
            r"replacement not found",
            r"content mismatch",
        ],
        L1Category.CONTEXT_MISSING: [
            r"context",
            r"missing.*information",
            r"insufficient",
            r"not enough context",
        ],
        L1Category.DEPENDENCY_BUILD: [
            r"module not found",
            r"ImportError",
            r"build failed",
            r"compilation error",
            r"dependency",
        ],
        L1Category.CONCURRENCY_ORDER: [
            r"concurrent",
            r"race condition",
            r"deadlock",
            r"message order",
            r"session.*conflict",
        ],
        L1Category.TEST_ASSERTION: [
            r"AssertionError",
            r"assert.*failed",
            r"expected.*but got",
            r"does not match",
        ],
        L1Category.FRAMEWORK_CONTRACT: [
            r"contract",
            r"interface",
            r"schema",
            r"validation failed",
        ],
        L1Category.HALLUCINATION: [
            r"hallucinat",
            r"imaginary",
            r"non-existent",
            r"fabricated",
        ],
    }
    
    # L2 根因规则
    L2_RULES = {
        # edit_failed 相关
        "target_missing": [
            r"old_string not found",
            r"target.*not.*found",
            r"does not contain",
        ],
        "file_dirty": [
            r"branch.*dirty",
            r"uncommitted",
            r"modified",
        ],
        "wrong_file": [
            r"wrong file",
            r"incorrect path",
        ],
        # tool_failed 相关
        "permission_denied": [
            r"permission denied",
            r"PermissionError",
            r"EACCES",
        ],
        "PATH_missing": [
            r"command not found",
            r"No such file",
            r"not in PATH",
        ],
        "timeout": [
            r"timeout",
            r"timed out",
            r"deadline exceeded",
        ],
        # runtime_failed 相关
        "message_order_conflict": [
            r"message order",
            r"out of order",
            r"sequence",
        ],
        "concurrent_session_write": [
            r"concurrent.*write",
            r"session.*conflict",
            r"race condition",
        ],
        "state_corruption": [
            r"corrupt",
            r"inconsistent",
            r"invalid state",
        ],
    }
    
    # 上下文提示规则
    CONTEXT_RULES = {
        "branch_dirty": [
            r"uncommitted",
            r"modified.*not.*staged",
            r"dirty",
        ],
        "PATH_missing": [
            r"PATH",
            r"command not found",
        ],
        "env_missing": [
            r"environment",
            r"env.*not set",
            r"missing.*variable",
        ],
        "network_issue": [
            r"network",
            r"connection",
            r"timeout",
        ],
    }
    
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.taxonomy_file = self.workspace / "config" / "failure_taxonomy.yaml"
        self.signatures_db = self.workspace / "memory" / "problem_signatures.jsonl"
        self.signatures_db.parent.mkdir(parents=True, exist_ok=True)
    
    def classify_l1(self, failure_type: str, stderr: str) -> L1Category:
        """
        L1 分类 - 确定高层类别
        
        Args:
            failure_type: 失败类型
            stderr: 错误输出
        
        Returns:
            L1Category
        """
        stderr_lower = stderr.lower()
        
        scores = {}
        for category, patterns in self.L1_RULES.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, stderr, re.IGNORECASE):
                    score += 1
            if score > 0:
                scores[category] = score
        
        if not scores:
            return L1Category.UNKNOWN
        
        # 返回得分最高的类别
        return max(scores, key=scores.get)
    
    def extract_l2(self, failure_type: str, stderr: str) -> Tuple[str, str, float]:
        """
        L2 提取 - 确定根因和上下文
        
        Returns:
            (root_cause, context_hint, confidence)
        """
        stderr_lower = stderr.lower()
        
        # 匹配根因
        root_cause = "unknown"
        root_confidence = 0.0
        
        for cause, patterns in self.L2_RULES.items():
            for pattern in patterns:
                if re.search(pattern, stderr, re.IGNORECASE):
                    root_cause = cause
                    root_confidence = 0.8
                    break
            if root_cause != "unknown":
                break
        
        # 匹配上下文
        context_hint = "none"
        context_confidence = 0.0
        
        for hint, patterns in self.CONTEXT_RULES.items():
            for pattern in patterns:
                if re.search(pattern, stderr, re.IGNORECASE):
                    context_hint = hint
                    context_confidence = 0.7
                    break
            if context_hint != "none":
                break
        
        # 综合置信度
        confidence = (root_confidence + context_confidence) / 2
        if confidence == 0:
            confidence = 0.3  # 最低置信度
        
        return root_cause, context_hint, confidence
    
    def generate_signature(
        self,
        failure_type: str,
        stderr: str,
        related_files: List[str]
    ) -> L2Signature:
        """
        生成完整的问题签名
        
        Args:
            failure_type: 失败类型
            stderr: 错误输出
            related_files: 相关文件
        
        Returns:
            L2Signature
        """
        # L1 分类
        l1_category = self.classify_l1(failure_type, stderr)
        
        # L2 提取
        root_cause, context_hint, confidence = self.extract_l2(failure_type, stderr)
        
        # 构建签名字符串
        file_hint = "_".join(sorted([Path(f).stem for f in related_files])) if related_files else "none"
        
        signature = f"{failure_type}+{root_cause}+{context_hint}+{l1_category.value}+{file_hint}"
        
        # 生成哈希
        signature_hash = hashlib.sha256(signature.encode()).hexdigest()[:16]
        
        # 记录匹配规则
        matching_rules = []
        if l1_category != L1Category.UNKNOWN:
            matching_rules.append(f"L1:{l1_category.value}")
        if root_cause != "unknown":
            matching_rules.append(f"L2:{root_cause}")
        if context_hint != "none":
            matching_rules.append(f"CTX:{context_hint}")
        
        return L2Signature(
            failure_type=failure_type,
            root_cause=root_cause,
            context_hint=context_hint,
            signature=signature,
            signature_hash=signature_hash,
            confidence=confidence,
            matching_rules=matching_rules
        )
    
    def find_similar_signatures(
        self,
        signature_hash: str,
        threshold: float = 0.8
    ) -> List[Dict]:
        """
        查找历史相似签名
        
        Args:
            signature_hash: 当前签名哈希
            threshold: 相似度阈值
        
        Returns:
            相似签名列表
        """
        similar = []
        
        if not self.signatures_db.exists():
            return similar
        
        with open(self.signatures_db) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    # 简单匹配：哈希前缀相同
                    if record.get("signature_hash", "")[:8] == signature_hash[:8]:
                        similar.append(record)
                except:
                    pass
        
        return similar
    
    def save_signature(self, signature: L2Signature, bundle_id: str):
        """保存签名到数据库"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "bundle_id": bundle_id,
            **signature.to_dict()
        }
        
        with open(self.signatures_db, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def get_signature_stats(self) -> Dict:
        """获取签名统计"""
        stats = {
            "total_signatures": 0,
            "by_l1_category": {},
            "by_root_cause": {},
            "high_confidence": 0,
        }
        
        if not self.signatures_db.exists():
            return stats
        
        with open(self.signatures_db) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    stats["total_signatures"] += 1
                    
                    # L1 分类统计
                    # 从 signature 中提取
                    sig = record.get("signature", "")
                    parts = sig.split("+")
                    if len(parts) >= 4:
                        l1 = parts[3]
                        stats["by_l1_category"][l1] = stats["by_l1_category"].get(l1, 0) + 1
                    
                    # 根因统计
                    root_cause = record.get("root_cause", "unknown")
                    stats["by_root_cause"][root_cause] = stats["by_root_cause"].get(root_cause, 0) + 1
                    
                    # 高置信度统计
                    if record.get("confidence", 0) >= 0.8:
                        stats["high_confidence"] += 1
                except:
                    pass
        
        return stats


# 便捷函数
def analyze_failure(
    workspace: Path,
    failure_type: str,
    stderr: str,
    related_files: List[str]
) -> L2Signature:
    """
    分析失败并生成签名
    
    便捷函数，一键分析
    """
    matcher = SignatureMatcher(workspace)
    return matcher.generate_signature(failure_type, stderr, related_files)


# CLI
if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Problem Signature Analyzer")
    parser.add_argument("--workspace", default=".", help="Workspace path")
    parser.add_argument("--test", action="store_true", help="Run test")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    
    args = parser.parse_args()
    
    matcher = SignatureMatcher(Path(args.workspace))
    
    if args.test:
        # 测试案例
        test_cases = [
            {
                "failure_type": "edit_failed",
                "stderr": "Error: old_string not found in file src/example.py",
                "related_files": ["src/example.py"],
            },
            {
                "failure_type": "tool_failed",
                "stderr": "PermissionError: [Errno 13] Permission denied: '/root/file'",
                "related_files": ["/root/file"],
            },
            {
                "failure_type": "runtime_failed",
                "stderr": "Concurrent session write detected: message order conflict",
                "related_files": ["session_manager.py"],
            },
        ]
        
        for case in test_cases:
            sig = matcher.generate_signature(
                case["failure_type"],
                case["stderr"],
                case["related_files"]
            )
            print(f"\nTest Case: {case['failure_type']}")
            print(f"  L1 Category: {matcher.classify_l1(case['failure_type'], case['stderr']).value}")
            print(f"  L2 Signature: {sig.signature}")
            print(f"  Hash: {sig.signature_hash}")
            print(f"  Confidence: {sig.confidence}")
            print(f"  Matching Rules: {sig.matching_rules}")
    
    if args.stats:
        stats = matcher.get_signature_stats()
        print("\nSignature Statistics:")
        print(json.dumps(stats, indent=2))
