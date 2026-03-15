"""
Knowledge Classifier - Knowledge 层分类器

将文件分类为 Knowledge 层，包括用户偏好、项目规则、决策等。
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class KnowledgeType(str, Enum):
    """Knowledge 类型"""
    USER_PREFERENCE = "user_preference"
    PROJECT_RULE = "project_rule"
    DECISION = "decision"
    TRUST_ANCHOR = "trust_anchor"
    CONSTRAINT = "constraint"
    EXPERIENCE = "experience"


@dataclass
class KnowledgeClassification:
    """Knowledge 分类结果"""
    file_path: str
    knowledge_type: KnowledgeType
    confidence: float
    reason: str
    tags: List[str]
    importance: float
    metadata: Dict[str, Any]


class KnowledgeClassifier:
    """Knowledge 层分类器"""
    
    # 用户偏好文件模式
    USER_PREFERENCE_PATTERNS = [
        r"USER\.md$",
        r"preferences/",
        r"user_",
        r"_preference",
    ]
    
    # 项目规则文件模式
    PROJECT_RULE_PATTERNS = [
        r"^POLICIES/",
        r"^policy/",
        r"^config/.*\.ya?ml$",
        r"^config/.*\.json$",
        r"policy\.md$",
        r"rules\.md$",
        r"constraints\.md$",
    ]
    
    # 决策文件模式
    DECISION_PATTERNS = [
        r"DECISIONS\.md$",
        r"decision/",
        r"decisions/",
        r"_decision\.md$",
        r"-decision-",
    ]
    
    # 信任锚点模式
    TRUST_ANCHOR_PATTERNS = [
        r"^trust-anchor/",
        r"trust_anchor",
        r"anchor\.md$",
        r"CURRENT_STATUS\.md$",
        r"CHECKPOINT\.md$",
    ]
    
    # 约束文件模式
    CONSTRAINT_PATTERNS = [
        r"CONSTRAINTS\.md$",
        r"constraint",
        r"boundary",
        r"AGENTS\.md$",
        r"SOUL\.md$",
        r"IDENTITY\.md$",
    ]
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
    
    def classify(self, file_path: str) -> Optional[KnowledgeClassification]:
        """分类文件为 Knowledge 类型"""
        path = Path(file_path)
        relative_path = str(path.relative_to(self.base_dir)) if path.is_absolute() else file_path
        
        # 检查用户偏好
        for pattern in self.USER_PREFERENCE_PATTERNS:
            if re.search(pattern, relative_path, re.IGNORECASE):
                return KnowledgeClassification(
                    file_path=file_path,
                    knowledge_type=KnowledgeType.USER_PREFERENCE,
                    confidence=0.8,
                    reason=f"Matched user preference pattern: {pattern}",
                    tags=["user_preference", "stable"],
                    importance=0.9,
                    metadata={"pattern": pattern}
                )
        
        # 检查项目规则
        for pattern in self.PROJECT_RULE_PATTERNS:
            if re.search(pattern, relative_path, re.IGNORECASE):
                return KnowledgeClassification(
                    file_path=file_path,
                    knowledge_type=KnowledgeType.PROJECT_RULE,
                    confidence=0.85,
                    reason=f"Matched project rule pattern: {pattern}",
                    tags=["project_rule", "config"],
                    importance=0.85,
                    metadata={"pattern": pattern}
                )
        
        # 检查决策
        for pattern in self.DECISION_PATTERNS:
            if re.search(pattern, relative_path, re.IGNORECASE):
                return KnowledgeClassification(
                    file_path=file_path,
                    knowledge_type=KnowledgeType.DECISION,
                    confidence=0.8,
                    reason=f"Matched decision pattern: {pattern}",
                    tags=["decision"],
                    importance=0.8,
                    metadata={"pattern": pattern}
                )
        
        # 检查信任锚点
        for pattern in self.TRUST_ANCHOR_PATTERNS:
            if re.search(pattern, relative_path, re.IGNORECASE):
                return KnowledgeClassification(
                    file_path=file_path,
                    knowledge_type=KnowledgeType.TRUST_ANCHOR,
                    confidence=0.9,
                    reason=f"Matched trust anchor pattern: {pattern}",
                    tags=["trust_anchor", "critical"],
                    importance=1.0,
                    metadata={"pattern": pattern}
                )
        
        # 检查约束
        for pattern in self.CONSTRAINT_PATTERNS:
            if re.search(pattern, relative_path, re.IGNORECASE):
                return KnowledgeClassification(
                    file_path=file_path,
                    knowledge_type=KnowledgeType.CONSTRAINT,
                    confidence=0.85,
                    reason=f"Matched constraint pattern: {pattern}",
                    tags=["constraint", "boundary"],
                    importance=0.9,
                    metadata={"pattern": pattern}
                )
        
        return None
    
    def classify_all(self, file_paths: List[str]) -> Dict[str, KnowledgeClassification]:
        """分类所有文件"""
        results = {}
        for file_path in file_paths:
            classification = self.classify(file_path)
            if classification:
                results[file_path] = classification
        return results
    
    def scan_and_classify(self, directory: str = None) -> Dict[str, KnowledgeClassification]:
        """扫描目录并分类"""
        scan_dir = Path(directory) if directory else self.base_dir
        results = {}
        
        for path in scan_dir.rglob("*"):
            if path.is_file() and path.suffix in [".md", ".yaml", ".yml", ".json"]:
                classification = self.classify(str(path))
                if classification:
                    results[str(path)] = classification
        
        return results
    
    def to_dict(self, classification: KnowledgeClassification) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(classification)


def main():
    """主函数"""
    import json
    
    classifier = KnowledgeClassifier(".")
    results = classifier.scan_and_classify()
    
    print(f"Found {len(results)} Knowledge files")
    
    # 按类型分组
    by_type = {}
    for path, classification in results.items():
        ktype = classification.knowledge_type.value
        if ktype not in by_type:
            by_type[ktype] = []
        by_type[ktype].append(path)
    
    for ktype, files in by_type.items():
        print(f"\n{ktype}: {len(files)} files")
        for f in files[:5]:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
