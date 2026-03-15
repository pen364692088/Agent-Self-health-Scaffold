"""
Truth/Knowledge/Retrieval Classifier

将记忆条目按 Truth/Knowledge/Retrieval 三层分类。
基于内容特征和元数据进行自动分类。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemorySourceKind,
    TruthKnowledgeRetrieval,
)


@dataclass
class ClassificationResult:
    """
    分类结果
    """
    layer: TruthKnowledgeRetrieval
    confidence: float  # 分类置信度
    reasons: List[str]  # 分类原因
    secondary_layer: Optional[TruthKnowledgeRetrieval] = None  # 次要层级（如果跨层）


class TruthKnowledgeRetrievalClassifier:
    """
    Truth/Knowledge/Retrieval 三层分类器
    
    分类规则：
    - Truth: 确定性事实，结构化，不易变
    - Knowledge: 规则、决策、偏好，可能有冲突，需要置信度
    - Retrieval: 检索事件、统计数据，用于评估和监控
    """
    
    # Truth 层特征
    TRUTH_INDICATORS = {
        "keywords": [
            "schema", "definition", "template", "format",
            "version", "config", "state",
            "定义", "模板", "配置", "状态",
        ],
        "extensions": [".schema.json", ".state.json", ".config.json"],
        "source_kinds": [
            MemorySourceKind.STATE,
            MemorySourceKind.CONFIG,
            MemorySourceKind.SCHEMA,
            MemorySourceKind.TEMPLATE,
            MemorySourceKind.METRICS,
        ],
    }
    
    # Knowledge 层特征
    KNOWLEDGE_INDICATORS = {
        "keywords": [
            "rule", "policy", "decision", "preference",
            "must", "should", "required", "禁止", "强制",
            "规则", "策略", "决策", "偏好",
            "fix", "solution", "workaround",
            "修复", "解决方案",
        ],
        "source_kinds": [
            MemorySourceKind.RULE,
            MemorySourceKind.POLICY,
            MemorySourceKind.DECISION_LOG,
            MemorySourceKind.PREFERENCE,
            MemorySourceKind.SESSION_LOG,
            MemorySourceKind.TECHNICAL_NOTE,
        ],
    }
    
    # Retrieval 层特征
    RETRIEVAL_INDICATORS = {
        "keywords": [
            "event", "recall", "retrieval", "search",
            "metrics", "stats", "regression",
            "事件", "召回", "检索", "统计",
        ],
        "extensions": [".jsonl", ".log"],
        "source_kinds": [
            MemorySourceKind.RETRIEVAL_EVENT,
            MemorySourceKind.DRIFT_EVENT,
            MemorySourceKind.EVOLUTION_EVENT,
        ],
    }
    
    def classify(self, record: MemoryRecord) -> ClassificationResult:
        """
        分类记忆条目
        
        Args:
            record: MemoryRecord 实例
            
        Returns:
            ClassificationResult
        """
        reasons = []
        scores = {
            TruthKnowledgeRetrieval.TRUTH: 0.0,
            TruthKnowledgeRetrieval.KNOWLEDGE: 0.0,
            TruthKnowledgeRetrieval.RETRIEVAL: 0.0,
        }
        
        # 1. 基于 source_kind 分类（最高权重）
        sk = record.source_kind
        if sk in self.TRUTH_INDICATORS["source_kinds"]:
            scores[TruthKnowledgeRetrieval.TRUTH] += 3.0
            reasons.append(f"source_kind={sk.value} → Truth")
        elif sk in self.KNOWLEDGE_INDICATORS["source_kinds"]:
            scores[TruthKnowledgeRetrieval.KNOWLEDGE] += 3.0
            reasons.append(f"source_kind={sk.value} → Knowledge")
        elif sk in self.RETRIEVAL_INDICATORS["source_kinds"]:
            scores[TruthKnowledgeRetrieval.RETRIEVAL] += 3.0
            reasons.append(f"source_kind={sk.value} → Retrieval")
        
        # 2. 基于内容关键词分类
        content_lower = record.content.lower()
        title_lower = record.title.lower()
        combined_text = f"{title_lower} {content_lower}"
        
        for keyword in self.TRUTH_INDICATORS["keywords"]:
            if keyword in combined_text:
                scores[TruthKnowledgeRetrieval.TRUTH] += 1.0
                reasons.append(f"keyword '{keyword}' → Truth")
        
        for keyword in self.KNOWLEDGE_INDICATORS["keywords"]:
            if keyword in combined_text:
                scores[TruthKnowledgeRetrieval.KNOWLEDGE] += 1.0
                reasons.append(f"keyword '{keyword}' → Knowledge")
        
        for keyword in self.RETRIEVAL_INDICATORS["keywords"]:
            if keyword in combined_text:
                scores[TruthKnowledgeRetrieval.RETRIEVAL] += 1.0
                reasons.append(f"keyword '{keyword}' → Retrieval")
        
        # 3. 基于文件扩展名分类
        ext = Path(record.source_file).suffix.lower()
        if ext in self.TRUTH_INDICATORS["extensions"]:
            scores[TruthKnowledgeRetrieval.TRUTH] += 2.0
            reasons.append(f"extension '{ext}' → Truth")
        if ext in self.RETRIEVAL_INDICATORS["extensions"]:
            scores[TruthKnowledgeRetrieval.RETRIEVAL] += 2.0
            reasons.append(f"extension '{ext}' → Retrieval")
        
        # 4. 基于元数据特征分类
        if record.tkr_layer != TruthKnowledgeRetrieval.KNOWLEDGE:  # 已经有预设值
            scores[record.tkr_layer] += 1.0
            reasons.append(f"pre-set tkr_layer={record.tkr_layer.value}")
        
        # 5. 基于内容结构分类
        structure_score = self._analyze_structure(record.content)
        scores[TruthKnowledgeRetrieval.TRUTH] += structure_score["truth"]
        scores[TruthKnowledgeRetrieval.KNOWLEDGE] += structure_score["knowledge"]
        scores[TruthKnowledgeRetrieval.RETRIEVAL] += structure_score["retrieval"]
        
        if structure_score["truth"] > 0:
            reasons.append("structured content (YAML/JSON) → Truth")
        
        # 确定最终分类
        max_score = max(scores.values())
        total_score = sum(scores.values())
        
        # 找到最高分的层级
        primary_layer = None
        for layer, score in scores.items():
            if score == max_score:
                primary_layer = layer
                break
        
        # 计算置信度
        confidence = max_score / total_score if total_score > 0 else 0.5
        
        # 检查是否有次要层级
        secondary_layer = None
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) > 1:
            if sorted_scores[1][1] > 0 and sorted_scores[1][1] >= max_score * 0.5:
                secondary_layer = sorted_scores[1][0]
        
        return ClassificationResult(
            layer=primary_layer or TruthKnowledgeRetrieval.KNOWLEDGE,
            confidence=min(confidence, 1.0),
            reasons=reasons[:5],  # 最多保留 5 个原因
            secondary_layer=secondary_layer,
        )
    
    def _analyze_structure(self, content: str) -> Dict[str, float]:
        """
        分析内容结构
        
        Returns:
            各层级的结构得分
        """
        scores = {
            "truth": 0.0,
            "knowledge": 0.0,
            "retrieval": 0.0,
        }
        
        # 检测 YAML/JSON 结构（Truth 特征）
        if content.strip().startswith("---"):
            scores["truth"] += 1.0
        if content.strip().startswith("{") or content.strip().startswith("["):
            scores["truth"] += 1.0
        
        # 检测 JSONL 格式（Retrieval 特征）
        lines = content.strip().split("\n")
        jsonl_count = 0
        for line in lines[:10]:
            if line.strip().startswith("{") and line.strip().endswith("}"):
                jsonl_count += 1
        if jsonl_count >= 3:
            scores["retrieval"] += 2.0
        
        # 检测 Markdown 标题结构（Knowledge 特征）
        heading_count = len(re.findall(r"^#{1,3}\s+", content, re.MULTILINE))
        if heading_count >= 3:
            scores["knowledge"] += 1.0
        
        # 检测代码块（Knowledge 特征）
        code_block_count = len(re.findall(r"```", content))
        if code_block_count >= 2:
            scores["knowledge"] += 1.0
        
        return scores
    
    def classify_batch(self, records: List[MemoryRecord]) -> List[ClassificationResult]:
        """
        批量分类
        
        Args:
            records: MemoryRecord 列表
            
        Returns:
            ClassificationResult 列表
        """
        return [self.classify(record) for record in records]
    
    def get_layer_distribution(self, records: List[MemoryRecord]) -> Dict[str, int]:
        """
        获取层级分布
        
        Args:
            records: MemoryRecord 列表
            
        Returns:
            各层级的数量统计
        """
        distribution = {
            TruthKnowledgeRetrieval.TRUTH.value: 0,
            TruthKnowledgeRetrieval.KNOWLEDGE.value: 0,
            TruthKnowledgeRetrieval.RETRIEVAL.value: 0,
        }
        
        for record in records:
            result = self.classify(record)
            distribution[result.layer.value] += 1
        
        return distribution
    
    def get_layer_statistics(self, records: List[MemoryRecord]) -> Dict[str, Any]:
        """
        获取层级统计信息
        
        Args:
            records: MemoryRecord 列表
            
        Returns:
            统计信息
        """
        results = self.classify_batch(records)
        
        # 按层级分组
        by_layer = {
            TruthKnowledgeRetrieval.TRUTH.value: [],
            TruthKnowledgeRetrieval.KNOWLEDGE.value: [],
            TruthKnowledgeRetrieval.RETRIEVAL.value: [],
        }
        
        for record, result in zip(records, results):
            by_layer[result.layer.value].append({
                "id": record.id,
                "source_file": record.source_file,
                "confidence": result.confidence,
            })
        
        # 计算统计信息
        stats = {
            "total": len(records),
            "distribution": {k: len(v) for k, v in by_layer.items()},
            "avg_confidence": sum(r.confidence for r in results) / len(results) if results else 0,
            "by_layer": by_layer,
        }
        
        return stats


def main():
    """主函数 - 用于测试"""
    import json
    from pathlib import Path
    
    # 导入 source_mapper
    from core.memory.source_mapper import SourceMapper
    
    # 获取 memory 目录路径
    repo_root = Path(__file__).parent.parent.parent
    memory_dir = repo_root / "memory"
    
    print(f"Loading records from: {memory_dir}")
    
    # 映射文件
    mapper = SourceMapper(str(memory_dir))
    records = mapper.map_all_files()
    
    print(f"Total records: {len(records)}")
    
    # 分类
    classifier = TruthKnowledgeRetrievalClassifier()
    stats = classifier.get_layer_statistics(records)
    
    print("\n=== Truth/Knowledge/Retrieval Classification ===")
    print(f"Total: {stats['total']}")
    print(f"Distribution: {json.dumps(stats['distribution'], indent=2)}")
    print(f"Average confidence: {stats['avg_confidence']:.2f}")
    
    # 保存报告
    report_path = repo_root / "docs" / "memory" / "TKR_CLASSIFICATION.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(stats, f, indent=2)
    
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
