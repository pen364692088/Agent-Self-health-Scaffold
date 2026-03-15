"""
Memory Source Mapper

将现有 memory/ 文件映射为 MemoryRecord。
只做映射，不做迁移，不影响现有系统运行。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    MemorySourceKind,
    MemoryTier,
    MemoryStatus,
    MemoryContentType,
    TruthKnowledgeRetrieval,
    MemorySource,
)


class SourceMapper:
    """
    源文件映射器
    
    将现有 memory/ 目录下的文件映射为 MemoryRecord 对象。
    """
    
    def __init__(self, memory_dir: str):
        """
        初始化映射器
        
        Args:
            memory_dir: memory 目录路径
        """
        self.memory_dir = Path(memory_dir)
        self._id_counter = 0
    
    def scan_directory(self) -> List[Dict[str, Any]]:
        """
        扫描 memory 目录
        
        Returns:
            文件信息列表
        """
        files = []
        
        for path in self.memory_dir.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(self.memory_dir)
                stat = path.stat()
                
                files.append({
                    "path": str(path),
                    "relative_path": str(rel_path),
                    "filename": path.name,
                    "extension": path.suffix,
                    "size": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime),
                })
        
        return files
    
    def map_file_to_record(self, file_info: Dict[str, Any], content: Optional[str] = None) -> Optional[MemoryRecord]:
        """
        将文件映射为 MemoryRecord
        
        Args:
            file_info: 文件信息
            content: 文件内容（可选，不提供则自动读取）
            
        Returns:
            MemoryRecord 或 None（如果无法映射）
        """
        path = file_info["path"]
        filename = file_info["filename"]
        extension = file_info["extension"]
        
        # 跳过不支持的文件类型
        if extension not in [".md", ".json", ".jsonl", ".log", ""]:
            return None
        
        # 读取内容
        if content is None:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                return None
        
        # 推断分类
        scope, scope_qualifier = self._infer_scope(path, content)
        source_kind = self._infer_source_kind(path, filename, content)
        content_type = self._infer_content_type(content)
        tkr_layer = self._infer_tkr_layer(path, filename, source_kind, content)
        
        # 提取标题和正文
        title, body = self._extract_title_and_body(filename, content)
        
        # 生成 ID
        record_id = self._generate_id(filename, file_info["mtime"])
        
        # 提取来源信息
        sources = self._extract_sources(path, content)
        
        # 提取元数据
        metadata = self._extract_metadata(content)
        
        return MemoryRecord(
            id=record_id,
            scope=scope,
            scope_qualifier=scope_qualifier,
            source_kind=source_kind,
            content_type=content_type,
            tkr_layer=tkr_layer,
            title=title,
            content=body,
            tags=self._extract_tags(content),
            source_file=str(file_info["relative_path"]),
            sources=sources,
            tier=self._infer_tier(content, file_info),
            status=MemoryStatus.ACTIVE,
            created_at=file_info["mtime"],  # 使用文件修改时间作为创建时间
            confidence=metadata.get("confidence", 0.5),
            importance=metadata.get("importance", 0.5),
            pinned=metadata.get("pinned", False),
            metadata=metadata,
        )
    
    def _generate_id(self, filename: str, mtime: datetime) -> str:
        """
        生成记忆 ID
        
        格式: mem_YYYYMMDD_XXX
        """
        self._id_counter += 1
        date_part = mtime.strftime("%Y%m%d")
        seq_part = f"{self._id_counter:03d}"
        return f"mem_{date_part}_{seq_part}"
    
    def _infer_scope(self, path: str, content: str) -> Tuple[MemoryScope, Optional[str]]:
        """
        推断作用域
        """
        path_lower = path.lower()
        content_lower = content.lower()
        
        # 项目特征
        project_indicators = {
            "openemotion": "openemotion",
            "emotiond": "emotiond",
            "openclaw": "openclaw",
            "agent-self-health": "agent_self_health",
        }
        
        for indicator, project_name in project_indicators.items():
            if indicator in path_lower or indicator in content_lower:
                return MemoryScope.PROJECTS, project_name
        
        # 领域特征
        domain_indicators = {
            "infra": "infra",
            "security": "security",
            "frontend": "frontend",
            "backend": "backend",
            "telegram": "telegram",
        }
        
        for indicator, domain_name in domain_indicators.items():
            if indicator in path_lower:
                return MemoryScope.DOMAINS, domain_name
        
        return MemoryScope.GLOBAL, None
    
    def _infer_source_kind(self, path: str, filename: str, content: str) -> MemorySourceKind:
        """
        推断来源类型
        """
        filename_lower = filename.lower()
        path_lower = path.lower()
        
        # 模板和 schema
        if "template" in filename_lower:
            return MemorySourceKind.TEMPLATE
        if "schema" in filename_lower:
            return MemorySourceKind.SCHEMA
        
        # 状态文件
        if filename_lower in ["session-state.md", "working-buffer.md", "working-buffer.md"]:
            return MemorySourceKind.STATE
        if filename_lower.endswith(".state.json") or ".state." in filename_lower:
            return MemorySourceKind.STATE
        
        # 配置文件
        if "config" in filename_lower:
            return MemorySourceKind.CONFIG
        
        # 统计文件
        if "stats" in filename_lower or "metrics" in filename_lower:
            return MemorySourceKind.METRICS
        
        # 事件日志
        if "events" in filename_lower:
            if "drift" in filename_lower:
                return MemorySourceKind.DRIFT_EVENT
            if "evolution" in path_lower:
                return MemorySourceKind.EVOLUTION_EVENT
            return MemorySourceKind.RETRIEVAL_EVENT
        
        if filename_lower.endswith(".log"):
            return MemorySourceKind.RETRIEVAL_EVENT
        
        if filename_lower.endswith(".jsonl"):
            return MemorySourceKind.RETRIEVAL_EVENT
        
        # 策略文档
        if "policy" in filename_lower:
            return MemorySourceKind.POLICY
        
        # 决策日志
        if "decision" in filename_lower:
            return MemorySourceKind.DECISION_LOG
        
        # 维护文档
        if "maintenance" in filename_lower:
            return MemorySourceKind.RULE
        
        # 技术笔记（按日期命名的文件）
        if re.match(r"\d{4}-\d{2}-\d{2}", filename_lower):
            if any(kw in filename_lower for kw in ["fix", "debug", "error", "bug"]):
                return MemorySourceKind.TECHNICAL_NOTE
            return MemorySourceKind.SESSION_LOG
        
        return MemorySourceKind.SESSION_LOG
    
    def _infer_content_type(self, content: str) -> MemoryContentType:
        """
        推断内容类型
        """
        content_lower = content.lower()
        
        # 规则特征
        rule_indicators = [
            "must", "should", "required", "禁止", "强制",
            "policy", "rule", "规范", "规则",
        ]
        if any(ind in content_lower for ind in rule_indicators):
            return MemoryContentType.RULE
        
        # 事实特征
        fact_indicators = [
            "version", "config", "schema", "definition",
            "版本", "配置", "定义",
        ]
        if any(ind in content_lower for ind in fact_indicators):
            return MemoryContentType.FACT
        
        # 偏好特征
        preference_indicators = [
            "prefer", "like", "favorite", "习惯", "偏好",
        ]
        if any(ind in content_lower for ind in preference_indicators):
            return MemoryContentType.PREFERENCE
        
        # 默认为反思
        return MemoryContentType.REFLECTION
    
    def _infer_tkr_layer(self, path: str, filename: str, source_kind: MemorySourceKind, content: str) -> TruthKnowledgeRetrieval:
        """
        推断 Truth/Knowledge/Retrieval 层
        """
        # Retrieval 层：事件日志、统计
        if source_kind in [
            MemorySourceKind.RETRIEVAL_EVENT,
            MemorySourceKind.DRIFT_EVENT,
            MemorySourceKind.EVOLUTION_EVENT,
            MemorySourceKind.METRICS,
        ]:
            return TruthKnowledgeRetrieval.RETRIEVAL
        
        # Truth 层：状态、配置、Schema、模板
        if source_kind in [
            MemorySourceKind.STATE,
            MemorySourceKind.CONFIG,
            MemorySourceKind.SCHEMA,
            MemorySourceKind.TEMPLATE,
        ]:
            return TruthKnowledgeRetrieval.TRUTH
        
        # Knowledge 层：规则、策略、会话日志、技术笔记
        if source_kind in [
            MemorySourceKind.RULE,
            MemorySourceKind.POLICY,
            MemorySourceKind.SESSION_LOG,
            MemorySourceKind.TECHNICAL_NOTE,
            MemorySourceKind.DECISION_LOG,
            MemorySourceKind.PREFERENCE,
        ]:
            return TruthKnowledgeRetrieval.KNOWLEDGE
        
        return TruthKnowledgeRetrieval.KNOWLEDGE
    
    def _infer_tier(self, content: str, file_info: Dict[str, Any]) -> MemoryTier:
        """
        推断分层
        """
        content_lower = content.lower()
        
        # 高价值标记
        if "pinned" in content_lower or "重要" in content_lower:
            return MemoryTier.HOT
        
        # 频繁更新的文件（近期修改）
        mtime = file_info["mtime"]
        age_days = (datetime.now() - mtime).days
        
        if age_days < 7:
            return MemoryTier.WARM
        elif age_days < 30:
            return MemoryTier.WARM
        else:
            return MemoryTier.COLD
    
    def _extract_title_and_body(self, filename: str, content: str) -> Tuple[str, str]:
        """
        提取标题和正文
        """
        lines = content.split("\n")
        
        # 尝试提取第一个标题
        title = filename
        for line in lines[:10]:
            if line.startswith("# "):
                title = line[2:].strip()
                break
        
        # 移除 YAML 头（如果有）
        body_lines = []
        in_yaml = False
        yaml_end = False
        
        for line in lines:
            if line.strip() == "---":
                if not in_yaml:
                    in_yaml = True
                    continue
                else:
                    yaml_end = True
                    in_yaml = False
                    continue
            
            if in_yaml:
                continue
            
            body_lines.append(line)
        
        body = "\n".join(body_lines).strip()
        
        return title, body
    
    def _extract_sources(self, path: str, content: str) -> List[MemorySource]:
        """
        提取来源信息
        """
        sources = []
        
        # 从文件名提取日期
        match = re.search(r"(\d{4}-\d{2}-\d{2})", path)
        if match:
            session_date = match.group(1)
            sources.append(MemorySource(
                session=session_date,
                evidence=f"Extracted from {path}",
            ))
        
        # 从内容提取 commit 引用
        commit_matches = re.findall(r"commit[:\s]+([a-f0-9]{7,40})", content, re.IGNORECASE)
        for commit in commit_matches[:3]:  # 最多提取 3 个
            sources.append(MemorySource(
                session=session_date if match else "",
                evidence=f"Referenced commit {commit}",
                commit=commit,
            ))
        
        return sources if sources else [MemorySource(
            session=datetime.now().strftime("%Y-%m-%d"),
            evidence="Auto-generated source",
        )]
    
    def _extract_tags(self, content: str) -> List[str]:
        """
        提取标签
        """
        tags = []
        
        # 常见标签关键词
        tag_keywords = [
            "fix", "bug", "feature", "refactor", "test",
            "mvp", "integration", "security", "performance",
            "api", "config", "policy", "rule",
        ]
        
        content_lower = content.lower()
        for keyword in tag_keywords:
            if keyword in content_lower:
                tags.append(keyword)
        
        return tags[:5]  # 最多 5 个标签
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        提取元数据
        """
        metadata = {}
        
        # 尝试解析 YAML 头
        if content.startswith("---"):
            lines = content.split("\n")
            yaml_lines = []
            in_yaml = False
            
            for line in lines[1:]:
                if line.strip() == "---":
                    break
                yaml_lines.append(line)
            
            yaml_content = "\n".join(yaml_lines)
            
            # 简单解析 YAML
            for line in yaml_lines:
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    if key in ["confidence", "importance"]:
                        try:
                            metadata[key] = float(value)
                        except ValueError:
                            pass
                    elif key == "pinned":
                        metadata["pinned"] = value.lower() in ["true", "yes", "1"]
        
        return metadata
    
    def map_all_files(self) -> List[MemoryRecord]:
        """
        映射所有文件
        
        Returns:
            MemoryRecord 列表
        """
        files = self.scan_directory()
        records = []
        
        for file_info in files:
            record = self.map_file_to_record(file_info)
            if record:
                records.append(record)
        
        return records
    
    def generate_asset_map(self) -> Dict[str, Any]:
        """
        生成资产映射报告
        
        Returns:
            映射报告字典
        """
        files = self.scan_directory()
        
        report = {
            "total_files": len(files),
            "by_extension": {},
            "by_source_kind": {},
            "by_scope": {},
            "by_tkr_layer": {},
            "by_tier": {},
            "records": [],
        }
        
        for file_info in files:
            ext = file_info["extension"] or "no_ext"
            report["by_extension"][ext] = report["by_extension"].get(ext, 0) + 1
            
            record = self.map_file_to_record(file_info)
            if record:
                # 按来源类型统计
                sk = record.source_kind.value
                report["by_source_kind"][sk] = report["by_source_kind"].get(sk, 0) + 1
                
                # 按作用域统计
                scope = record.scope.value
                report["by_scope"][scope] = report["by_scope"].get(scope, 0) + 1
                
                # 按 TKR 层统计
                tkr = record.tkr_layer.value
                report["by_tkr_layer"][tkr] = report["by_tkr_layer"].get(tkr, 0) + 1
                
                # 按分层统计
                tier = record.tier.value
                report["by_tier"][tier] = report["by_tier"].get(tier, 0) + 1
                
                report["records"].append({
                    "id": record.id,
                    "source_file": record.source_file,
                    "source_kind": sk,
                    "scope": scope,
                    "tkr_layer": tkr,
                    "tier": tier,
                })
        
        return report


def main():
    """主函数 - 用于测试"""
    import json
    
    # 获取 memory 目录路径
    repo_root = Path(__file__).parent.parent.parent
    memory_dir = repo_root / "memory"
    
    print(f"Scanning memory directory: {memory_dir}")
    
    mapper = SourceMapper(str(memory_dir))
    report = mapper.generate_asset_map()
    
    print("\n=== Memory Asset Map Report ===")
    print(f"Total files: {report['total_files']}")
    print(f"\nBy extension: {json.dumps(report['by_extension'], indent=2)}")
    print(f"\nBy source kind: {json.dumps(report['by_source_kind'], indent=2)}")
    print(f"\nBy scope: {json.dumps(report['by_scope'], indent=2)}")
    print(f"\nBy TKR layer: {json.dumps(report['by_tkr_layer'], indent=2)}")
    print(f"\nBy tier: {json.dumps(report['by_tier'], indent=2)}")
    
    # 保存报告
    report_path = repo_root / "docs" / "memory" / "MEMORY_ASSET_MAP.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
