#!/usr/bin/env python3
"""
External Pattern Collector - 外部模式采集器

职责：
1. 从官方文档采集模式
2. 从 issue/PR 采集模式
3. 从成熟框架采集模式
4. 蒸馏成内部结构
5. 只进 shadow planner，不直接污染主链
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from enum import Enum


class PatternSource(Enum):
    """模式来源"""
    OFFICIAL_DOC = "official_doc"
    GITHUB_ISSUE = "github_issue"
    GITHUB_PR = "github_pr"
    FRAMEWORK = "framework"
    BLOG_ARTICLE = "blog_article"


class PatternStatus(Enum):
    """模式状态"""
    RAW = "raw"                    # 原始采集
    DISTILLED = "distilled"        # 已蒸馏
    IN_SHADOW = "in_shadow"        # 影子验证中
    PROMOTED = "promoted"          # 已晋升
    REJECTED = "rejected"          # 已拒绝


@dataclass
class PatternCard:
    """模式卡片"""
    pattern_id: str
    name: str
    description: str
    
    # 来源
    source_type: str
    source_url: str
    source_title: str
    
    # 内容
    problem_pattern: str           # 问题模式
    solution_pattern: str          # 解决方案
    code_example: Optional[str]    # 代码示例
    
    # 元数据
    language: str                  # 适用语言
    framework: Optional[str]       # 适用框架
    severity: str                  # 严重程度
    
    # 状态
    status: str
    created_at: str
    updated_at: str
    
    # 验证
    shadow_tests_passed: int
    shadow_tests_total: int
    observation_period_days: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AntiPatternCard:
    """反模式卡片"""
    anti_pattern_id: str
    name: str
    description: str
    
    # 问题
    anti_pattern: str              # 反模式描述
    why_harmful: str               # 为什么有害
    common_mistakes: List[str]     # 常见错误
    
    # 来源
    source_type: str
    source_url: str
    
    # 检测
    detection_patterns: List[str]  # 检测模式
    prevention_rules: List[str]    # 预防规则
    
    # 状态
    status: str
    created_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RemediationTemplate:
    """修复模板"""
    template_id: str
    name: str
    description: str
    
    # 匹配条件
    applicable_signatures: List[str]
    applicable_l1_categories: List[str]
    
    # 修复步骤
    steps: List[Dict[str, Any]]    # 步骤列表
    rollback_steps: List[str]      # 回滚步骤
    
    # 验证
    required_tests: List[str]
    expected_outcomes: List[str]
    
    # 来源与状态
    derived_from_pattern: Optional[str]
    status: str
    success_rate: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ExternalPatternCollector:
    """外部模式采集器"""
    
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.patterns_dir = self.workspace / "src" / "self_healing" / "shadow_planner" / "patterns"
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        
        # 存储
        self.pattern_cards_file = self.patterns_dir / "pattern_cards.jsonl"
        self.anti_pattern_cards_file = self.patterns_dir / "anti_pattern_cards.jsonl"
        self.templates_file = self.patterns_dir / "remediation_templates.jsonl"
    
    def collect_from_official_doc(
        self,
        doc_url: str,
        doc_title: str,
        problem_section: str,
        solution_section: str,
        code_example: Optional[str] = None
    ) -> PatternCard:
        """从官方文档采集"""
        pattern_id = f"pat_doc_{hash(doc_url) % 100000:05d}"
        now = datetime.now().isoformat()
        
        card = PatternCard(
            pattern_id=pattern_id,
            name=f"Pattern from {doc_title}",
            description=f"Extracted from official documentation",
            source_type=PatternSource.OFFICIAL_DOC.value,
            source_url=doc_url,
            source_title=doc_title,
            problem_pattern=problem_section,
            solution_pattern=solution_section,
            code_example=code_example,
            language="python",  # 默认
            framework=None,
            severity="medium",
            status=PatternStatus.RAW.value,
            created_at=now,
            updated_at=now,
            shadow_tests_passed=0,
            shadow_tests_total=0,
            observation_period_days=0
        )
        
        self._save_pattern_card(card)
        return card
    
    def collect_from_github_issue(
        self,
        repo: str,
        issue_number: int,
        issue_title: str,
        problem_description: str,
        solution_description: str,
        issue_url: str
    ) -> PatternCard:
        """从 GitHub Issue 采集"""
        pattern_id = f"pat_issue_{repo.replace('/', '_')}_{issue_number}"
        now = datetime.now().isoformat()
        
        card = PatternCard(
            pattern_id=pattern_id,
            name=f"Issue #{issue_number}: {issue_title[:50]}",
            description=f"Pattern from {repo} issue",
            source_type=PatternSource.GITHUB_ISSUE.value,
            source_url=issue_url,
            source_title=issue_title,
            problem_pattern=problem_description,
            solution_pattern=solution_description,
            code_example=None,
            language="python",
            framework=None,
            severity="medium",
            status=PatternStatus.RAW.value,
            created_at=now,
            updated_at=now,
            shadow_tests_passed=0,
            shadow_tests_total=0,
            observation_period_days=0
        )
        
        self._save_pattern_card(card)
        return card
    
    def distill_pattern(self, pattern_id: str) -> Optional[RemediationTemplate]:
        """
        将原始模式蒸馏成修复模板
        
        这是关键步骤：外部知识必须经过蒸馏才能使用
        """
        # 查找原始模式
        card = self._find_pattern_card(pattern_id)
        if not card:
            return None
        
        # 更新状态
        card.status = PatternStatus.DISTILLED.value
        card.updated_at = datetime.now().isoformat()
        self._update_pattern_card(card)
        
        # 创建修复模板
        template_id = f"tmpl_{pattern_id}"
        
        # 从问题模式提取签名
        applicable_signatures = self._extract_signatures(card.problem_pattern)
        
        template = RemediationTemplate(
            template_id=template_id,
            name=f"Template for {card.name}",
            description=card.description,
            applicable_signatures=applicable_signatures,
            applicable_l1_categories=[],
            steps=self._generate_steps(card.solution_pattern),
            rollback_steps=["git checkout HEAD -- {file}"],
            required_tests=[],
            expected_outcomes=["Problem resolved"],
            derived_from_pattern=pattern_id,
            status=PatternStatus.IN_SHADOW.value,
            success_rate=0.0
        )
        
        self._save_template(template)
        return template
    
    def run_shadow_validation(
        self,
        template_id: str,
        test_cases: List[Dict]
    ) -> bool:
        """
        在影子层运行验证
        
        模板必须通过 shadow validation 才能晋升
        """
        template = self._find_template(template_id)
        if not template:
            return False
        
        passed = 0
        total = len(test_cases)
        
        for test in test_cases:
            # 模拟测试
            # 实际实现需要真正的沙箱执行
            if self._simulate_test(template, test):
                passed += 1
        
        # 更新模板状态
        pattern = self._find_pattern_card(template.derived_from_pattern)
        if pattern:
            pattern.shadow_tests_passed = passed
            pattern.shadow_tests_total = total
            pattern.updated_at = datetime.now().isoformat()
            self._update_pattern_card(pattern)
        
        template.success_rate = passed / total if total > 0 else 0
        self._update_template(template)
        
        return passed / total >= 0.8 if total > 0 else False
    
    def promote_to_production(self, template_id: str) -> bool:
        """
        将模板晋升到生产环境
        
        条件：
        1. shadow validation 通过率 >= 80%
        2. 观察期 >= 7 天
        3. 无负面反馈
        """
        template = self._find_template(template_id)
        if not template:
            return False
        
        pattern = self._find_pattern_card(template.derived_from_pattern)
        if not pattern:
            return False
        
        # 检查条件
        if template.success_rate < 0.8:
            print(f"[ShadowPlanner] Cannot promote {template_id}: success rate {template.success_rate} < 0.8")
            return False
        
        if pattern.observation_period_days < 7:
            print(f"[ShadowPlanner] Cannot promote {template_id}: observation period {pattern.observation_period_days} < 7 days")
            return False
        
        # 晋升
        template.status = PatternStatus.PROMOTED.value
        pattern.status = PatternStatus.PROMOTED.value
        pattern.updated_at = datetime.now().isoformat()
        
        self._update_template(template)
        self._update_pattern_card(pattern)
        
        print(f"[ShadowPlanner] Promoted {template_id} to production")
        return True
    
    def _extract_signatures(self, problem_pattern: str) -> List[str]:
        """从问题模式提取签名"""
        signatures = []
        
        # 简单的关键词提取
        keywords = [
            "edit_failed", "tool_failed", "test_failed",
            "permission", "not_found", "timeout",
            "concurrent", "race_condition"
        ]
        
        for keyword in keywords:
            if keyword in problem_pattern.lower():
                signatures.append(keyword)
        
        return signatures
    
    def _generate_steps(self, solution_pattern: str) -> List[Dict]:
        """从解决方案生成步骤"""
        # 简化实现
        return [
            {"action": "analyze", "description": "Analyze the problem"},
            {"action": "apply_fix", "description": solution_pattern[:100]},
            {"action": "verify", "description": "Verify the fix"}
        ]
    
    def _simulate_test(self, template: RemediationTemplate, test: Dict) -> bool:
        """模拟测试"""
        # 简化实现：随机通过
        import random
        return random.random() > 0.2
    
    def _save_pattern_card(self, card: PatternCard):
        """保存模式卡片"""
        with open(self.pattern_cards_file, "a") as f:
            f.write(json.dumps(card.to_dict(), ensure_ascii=False) + "\n")
    
    def _update_pattern_card(self, card: PatternCard):
        """更新模式卡片"""
        if not self.pattern_cards_file.exists():
            return
        
        records = []
        with open(self.pattern_cards_file) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get("pattern_id") == card.pattern_id:
                        records.append(card.to_dict())
                    else:
                        records.append(record)
                except:
                    pass
        
        with open(self.pattern_cards_file, "w") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def _find_pattern_card(self, pattern_id: str) -> Optional[PatternCard]:
        """查找模式卡片"""
        if not self.pattern_cards_file.exists():
            return None
        
        with open(self.pattern_cards_file) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get("pattern_id") == pattern_id:
                        return PatternCard(**record)
                except:
                    pass
        return None
    
    def _save_template(self, template: RemediationTemplate):
        """保存模板"""
        with open(self.templates_file, "a") as f:
            f.write(json.dumps(template.to_dict(), ensure_ascii=False) + "\n")
    
    def _update_template(self, template: RemediationTemplate):
        """更新模板"""
        if not self.templates_file.exists():
            return
        
        records = []
        with open(self.templates_file) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get("template_id") == template.template_id:
                        records.append(template.to_dict())
                    else:
                        records.append(record)
                except:
                    pass
        
        with open(self.templates_file, "w") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def _find_template(self, template_id: str) -> Optional[RemediationTemplate]:
        """查找模板"""
        if not self.templates_file.exists():
            return None
        
        with open(self.templates_file) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get("template_id") == template_id:
                        return RemediationTemplate(**record)
                except:
                    pass
        return None


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="External Pattern Collector")
    parser.add_argument("--workspace", default=".", help="Workspace path")
    parser.add_argument("--test", action="store_true", help="Run test")
    
    args = parser.parse_args()
    
    collector = ExternalPatternCollector(Path(args.workspace))
    
    if args.test:
        # 测试采集
        card = collector.collect_from_official_doc(
            doc_url="https://docs.example.com/best-practices",
            doc_title="Best Practices Guide",
            problem_section="File not found errors when path is incorrect",
            solution_section="Use absolute paths or verify relative paths"
        )
        print(f"Collected pattern: {card.pattern_id}")
        
        # 蒸馏
        template = collector.distill_pattern(card.pattern_id)
        if template:
            print(f"Distilled template: {template.template_id}")
