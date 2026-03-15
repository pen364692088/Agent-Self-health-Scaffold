#!/usr/bin/env python3
"""
Evolution Memory - 经验沉淀与预防系统

职责：
1. 问题记忆（signature、触发条件、场景）
2. 成功修复记忆（方案、前提、验证结果）
3. 失败修复记忆（误修案例、禁用条件）
4. 预防规则（preflight 检查、高危保护）
"""

import json
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """记忆类型"""
    PROBLEM = "problem"           # 问题记忆
    SUCCESS = "success"           # 成功修复
    FAILURE = "failure"           # 失败修复
    PREVENTION = "prevention"     # 预防规则


@dataclass
class ProblemMemory:
    """问题记忆"""
    memory_id: str
    signature: str
    signature_hash: str
    
    # 触发条件
    failure_type: str
    root_cause: str
    context_hint: str
    
    # 场景
    trigger_patterns: List[str]   # 触发模式
    affected_files: List[str]     # 影响文件
    environment_conditions: Dict[str, str]
    
    # 影响范围
    severity: str
    scope: str                    # local / module / system
    
    # 元数据
    first_seen: str
    last_seen: str
    occurrence_count: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SuccessMemory:
    """成功修复记忆"""
    memory_id: str
    signature: str
    
    # 方案
    remedy_name: str
    remedy_description: str
    action_type: str
    action_params: Dict[str, Any]
    
    # 成功前提
    preconditions: List[str]
    required_context: List[str]
    
    # 验证结果
    validation_results: List[Dict]  # Gate A/B/C 结果
    sandbox_report_id: str
    
    # 成本
    execution_time_ms: int
    lines_changed: int
    human_intervention_required: bool
    
    # 统计
    success_count: int
    first_success: str
    last_success: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class FailureMemory:
    """失败修复记忆"""
    memory_id: str
    signature: str
    
    # 失败的方案
    attempted_remedy: str
    failure_reason: str
    
    # 禁用条件
    forbidden_conditions: List[str]
    
    # 误修案例
    false_positive_description: str
    damage_caused: List[str]
    
    # 元数据
    timestamp: str
    lesson_learned: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PreventionRule:
    """预防规则"""
    rule_id: str
    name: str
    description: str
    
    # 触发条件
    trigger_signatures: List[str]
    trigger_patterns: List[str]
    
    # 预防措施
    preflight_checks: List[str]
    required_confirmations: List[str]
    auto_remediation_level: str  # L0-L3
    
    # 保护规则
    protected_paths: List[str]
    required_tests: List[str]
    
    # 元数据
    created_at: str
    updated_at: str
    hit_count: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


class EvolutionMemory:
    """经验沉淀系统"""
    
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.memory_dir = self.workspace / "memory" / "evolution"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 四类记忆存储
        self.problem_db = self.memory_dir / "problems.jsonl"
        self.success_db = self.memory_dir / "successes.jsonl"
        self.failure_db = self.memory_dir / "failures.jsonl"
        self.prevention_db = self.memory_dir / "prevention_rules.jsonl"
        
        # 索引
        self._signature_index: Dict[str, List[str]] = {}
        self._load_index()
    
    def _load_index(self):
        """加载签名索引"""
        for db_file, memory_type in [
            (self.problem_db, "problem"),
            (self.success_db, "success"),
            (self.failure_db, "failure"),
        ]:
            if db_file.exists():
                with open(db_file) as f:
                    for line in f:
                        try:
                            record = json.loads(line.strip())
                            sig = record.get("signature", "")
                            if sig:
                                if sig not in self._signature_index:
                                    self._signature_index[sig] = []
                                self._signature_index[sig].append(memory_type)
                        except:
                            pass
    
    def record_problem(
        self,
        signature: str,
        failure_type: str,
        root_cause: str,
        context_hint: str,
        trigger_patterns: List[str],
        affected_files: List[str],
        environment: Dict[str, str],
        severity: str = "medium",
        scope: str = "local"
    ) -> ProblemMemory:
        """记录问题"""
        now = datetime.now().isoformat()
        
        # 检查是否已存在
        existing = self.find_problem_by_signature(signature)
        if existing:
            # 更新计数
            existing.occurrence_count += 1
            existing.last_seen = now
            existing.affected_files = list(set(existing.affected_files + affected_files))
            self._update_record(self.problem_db, existing.memory_id, existing.to_dict())
            return existing
        
        # 创建新记录
        memory = ProblemMemory(
            memory_id=f"prob_{hash(signature) % 100000:05d}",
            signature=signature,
            signature_hash=hashlib.sha256(signature.encode()).hexdigest()[:16],
            failure_type=failure_type,
            root_cause=root_cause,
            context_hint=context_hint,
            trigger_patterns=trigger_patterns,
            affected_files=affected_files,
            environment_conditions=environment,
            severity=severity,
            scope=scope,
            first_seen=now,
            last_seen=now,
            occurrence_count=1
        )
        
        self._append_record(self.problem_db, memory.to_dict())
        
        # 更新索引
        if signature not in self._signature_index:
            self._signature_index[signature] = []
        if "problem" not in self._signature_index[signature]:
            self._signature_index[signature].append("problem")
        
        return memory
    
    def record_success(
        self,
        signature: str,
        remedy_name: str,
        remedy_description: str,
        action_type: str,
        action_params: Dict[str, Any],
        preconditions: List[str],
        validation_results: List[Dict],
        sandbox_report_id: str,
        execution_time_ms: int,
        lines_changed: int
    ) -> SuccessMemory:
        """记录成功修复"""
        now = datetime.now().isoformat()
        
        # 检查是否已存在
        existing = self.find_success_by_signature_and_remedy(signature, remedy_name)
        if existing:
            existing.success_count += 1
            existing.last_success = now
            self._update_record(self.success_db, existing.memory_id, existing.to_dict())
            return existing
        
        memory = SuccessMemory(
            memory_id=f"succ_{hash(signature + remedy_name) % 100000:05d}",
            signature=signature,
            remedy_name=remedy_name,
            remedy_description=remedy_description,
            action_type=action_type,
            action_params=action_params,
            preconditions=preconditions,
            required_context=[],
            validation_results=validation_results,
            sandbox_report_id=sandbox_report_id,
            execution_time_ms=execution_time_ms,
            lines_changed=lines_changed,
            human_intervention_required=False,
            success_count=1,
            first_success=now,
            last_success=now
        )
        
        self._append_record(self.success_db, memory.to_dict())
        
        if signature not in self._signature_index:
            self._signature_index[signature] = []
        if "success" not in self._signature_index[signature]:
            self._signature_index[signature].append("success")
        
        return memory
    
    def record_failure(
        self,
        signature: str,
        attempted_remedy: str,
        failure_reason: str,
        forbidden_conditions: List[str],
        false_positive_description: str,
        damage_caused: List[str],
        lesson_learned: str
    ) -> FailureMemory:
        """记录失败修复"""
        memory = FailureMemory(
            memory_id=f"fail_{hash(signature + attempted_remedy) % 100000:05d}",
            signature=signature,
            attempted_remedy=attempted_remedy,
            failure_reason=failure_reason,
            forbidden_conditions=forbidden_conditions,
            false_positive_description=false_positive_description,
            damage_caused=damage_caused,
            timestamp=datetime.now().isoformat(),
            lesson_learned=lesson_learned
        )
        
        self._append_record(self.failure_db, memory.to_dict())
        
        if signature not in self._signature_index:
            self._signature_index[signature] = []
        if "failure" not in self._signature_index[signature]:
            self._signature_index[signature].append("failure")
        
        return memory
    
    def create_prevention_rule(
        self,
        name: str,
        description: str,
        trigger_signatures: List[str],
        trigger_patterns: List[str],
        preflight_checks: List[str],
        protected_paths: List[str],
        auto_level: str = "L0"
    ) -> PreventionRule:
        """创建预防规则"""
        now = datetime.now().isoformat()
        
        rule = PreventionRule(
            rule_id=f"prev_{hash(name) % 100000:05d}",
            name=name,
            description=description,
            trigger_signatures=trigger_signatures,
            trigger_patterns=trigger_patterns,
            preflight_checks=preflight_checks,
            required_confirmations=[],
            auto_remediation_level=auto_level,
            protected_paths=protected_paths,
            required_tests=[],
            created_at=now,
            updated_at=now,
            hit_count=0
        )
        
        self._append_record(self.prevention_db, rule.to_dict())
        return rule
    
    def find_problem_by_signature(self, signature: str) -> Optional[ProblemMemory]:
        """根据签名查找问题"""
        if not self.problem_db.exists():
            return None
        
        with open(self.problem_db) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get("signature") == signature:
                        return ProblemMemory(**record)
                except:
                    pass
        return None
    
    def find_success_by_signature_and_remedy(
        self,
        signature: str,
        remedy_name: str
    ) -> Optional[SuccessMemory]:
        """查找成功修复"""
        if not self.success_db.exists():
            return None
        
        with open(self.success_db) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if (record.get("signature") == signature and
                        record.get("remedy_name") == remedy_name):
                        return SuccessMemory(**record)
                except:
                    pass
        return None
    
    def get_successful_remedies(self, signature: str) -> List[SuccessMemory]:
        """获取某签名的所有成功修复"""
        remedies = []
        
        if not self.success_db.exists():
            return remedies
        
        with open(self.success_db) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get("signature") == signature:
                        remedies.append(SuccessMemory(**record))
                except:
                    pass
        
        # 按成功率排序
        return sorted(remedies, key=lambda x: x.success_count, reverse=True)
    
    def check_prevention_rules(
        self,
        signature: str,
        file_path: str,
        action_type: str
    ) -> List[PreventionRule]:
        """检查是否命中预防规则"""
        matched_rules = []
        
        if not self.prevention_db.exists():
            return matched_rules
        
        with open(self.prevention_db) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    
                    # 检查签名匹配
                    if signature in record.get("trigger_signatures", []):
                        matched_rules.append(PreventionRule(**record))
                        continue
                    
                    # 检查路径匹配
                    for protected in record.get("protected_paths", []):
                        if protected in file_path:
                            matched_rules.append(PreventionRule(**record))
                            break
                except:
                    pass
        
        return matched_rules
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        stats = {
            "total_problems": 0,
            "total_successes": 0,
            "total_failures": 0,
            "total_prevention_rules": 0,
            "unique_signatures": len(self._signature_index),
            "high_occurrence_problems": [],
            "top_successful_remedies": [],
        }
        
        # 统计问题
        if self.problem_db.exists():
            with open(self.problem_db) as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        stats["total_problems"] += 1
                        if record.get("occurrence_count", 0) > 5:
                            stats["high_occurrence_problems"].append({
                                "signature": record["signature"],
                                "count": record["occurrence_count"]
                            })
                    except:
                        pass
        
        # 统计成功
        if self.success_db.exists():
            with open(self.success_db) as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        stats["total_successes"] += 1
                        stats["top_successful_remedies"].append({
                            "signature": record["signature"],
                            "remedy": record["remedy_name"],
                            "count": record.get("success_count", 0)
                        })
                    except:
                        pass
            
            # 排序
            stats["top_successful_remedies"].sort(
                key=lambda x: x["count"],
                reverse=True
            )
            stats["top_successful_remedies"] = stats["top_successful_remedies"][:10]
        
        # 统计失败
        if self.failure_db.exists():
            with open(self.failure_db) as f:
                for line in f:
                    try:
                        stats["total_failures"] += 1
                    except:
                        pass
        
        # 统计规则
        if self.prevention_db.exists():
            with open(self.prevention_db) as f:
                for line in f:
                    try:
                        stats["total_prevention_rules"] += 1
                    except:
                        pass
        
        return stats
    
    def _append_record(self, db_file: Path, record: Dict):
        """追加记录"""
        with open(db_file, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def _update_record(self, db_file: Path, memory_id: str, new_record: Dict):
        """更新记录（简单实现：重写整个文件）"""
        if not db_file.exists():
            return
        
        records = []
        with open(db_file) as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get("memory_id") == memory_id:
                        records.append(new_record)
                    else:
                        records.append(record)
                except:
                    pass
        
        with open(db_file, "w") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evolution Memory")
    parser.add_argument("--workspace", default=".", help="Workspace path")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    
    args = parser.parse_args()
    
    memory = EvolutionMemory(Path(args.workspace))
    
    if args.stats:
        stats = memory.get_memory_stats()
        print(json.dumps(stats, indent=2))
