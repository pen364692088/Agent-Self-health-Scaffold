"""
Agent Profile Management

管理 Agent 身份、能力、记忆空间与运行时配置。

Author: Agent-Self-health-Scaffold
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import json


@dataclass
class Capability:
    """Agent 能力"""
    name: str
    level: str = "intermediate"
    description: str = ""


@dataclass
class MemoryConfig:
    """私有记忆空间配置"""
    memory_root: str
    instruction_rules_file: str = "instruction_rules.yaml"
    handoff_file: str = "handoff.md"
    execution_state_file: str = "execution_state.json"
    long_term_memory_dir: str = "long_term"


@dataclass
class RuntimeConfig:
    """运行时配置"""
    max_retries: int = 3
    timeout_seconds: int = 300
    enable_mutation_guard: bool = True
    enable_canonical_guard: bool = True
    allowed_mutation_paths: List[str] = field(default_factory=list)


@dataclass
class WorkingRules:
    """工作规则"""
    must_do: List[str] = field(default_factory=list)
    must_not_do: List[str] = field(default_factory=list)


@dataclass
class AgentProfile:
    """
    Agent Profile
    
    定义 Agent 的身份、能力、记忆空间与运行时配置。
    """
    agent_id: str
    name: str
    role: str
    description: str = ""
    capabilities: List[Capability] = field(default_factory=list)
    memory_config: Optional[MemoryConfig] = None
    runtime_config: RuntimeConfig = field(default_factory=RuntimeConfig)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    working_rules: WorkingRules = field(default_factory=WorkingRules)
    status: str = "inactive"
    pilot: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "capabilities": [
                {"name": c.name, "level": c.level, "description": c.description}
                for c in self.capabilities
            ],
            "memory_config": {
                "memory_root": self.memory_config.memory_root,
                "instruction_rules_file": self.memory_config.instruction_rules_file,
                "handoff_file": self.memory_config.handoff_file,
                "execution_state_file": self.memory_config.execution_state_file,
                "long_term_memory_dir": self.memory_config.long_term_memory_dir,
            } if self.memory_config else None,
            "runtime_config": {
                "max_retries": self.runtime_config.max_retries,
                "timeout_seconds": self.runtime_config.timeout_seconds,
                "enable_mutation_guard": self.runtime_config.enable_mutation_guard,
                "enable_canonical_guard": self.runtime_config.enable_canonical_guard,
                "allowed_mutation_paths": self.runtime_config.allowed_mutation_paths,
            },
            "inputs": self.inputs,
            "outputs": self.outputs,
            "working_rules": {
                "must_do": self.working_rules.must_do,
                "must_not_do": self.working_rules.must_not_do,
            },
            "status": self.status,
            "pilot": self.pilot,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def get_memory_root_path(self, project_root: Path) -> Path:
        """获取私有记忆空间根路径"""
        if self.memory_config:
            return project_root / self.memory_config.memory_root
        return project_root / "memory" / "agents" / self.agent_id
    
    def get_instruction_rules_path(self, project_root: Path) -> Path:
        """获取指令规则文件路径"""
        memory_root = self.get_memory_root_path(project_root)
        if self.memory_config:
            return memory_root / self.memory_config.instruction_rules_file
        return memory_root / "instruction_rules.yaml"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentProfile":
        """从字典创建"""
        capabilities = [
            Capability(**c) for c in data.get("capabilities", [])
        ]
        
        memory_config = None
        if data.get("memory_config"):
            memory_config = MemoryConfig(**data["memory_config"])
        
        runtime_config = RuntimeConfig(**data.get("runtime_config", {}))
        working_rules = WorkingRules(**data.get("working_rules", {}))
        
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            role=data["role"],
            description=data.get("description", ""),
            capabilities=capabilities,
            memory_config=memory_config,
            runtime_config=runtime_config,
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            working_rules=working_rules,
            status=data.get("status", "inactive"),
            pilot=data.get("pilot", False),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )
    
    @classmethod
    def from_json_file(cls, path: Path) -> "AgentProfile":
        """从 JSON 文件加载"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def save_to_json_file(self, path: Path) -> None:
        """保存到 JSON 文件"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())


class AgentProfileRegistry:
    """
    Agent Profile 注册表
    
    管理所有 Agent Profile 的加载、查询和持久化。
    """
    
    def __init__(self, project_root: Path, registry_dir: str = "agents"):
        self.project_root = project_root
        self.registry_dir = project_root / registry_dir
        self.profiles: Dict[str, AgentProfile] = {}
    
    def load_all(self) -> int:
        """加载所有 Agent Profile"""
        if not self.registry_dir.exists():
            return 0
        
        count = 0
        for profile_file in self.registry_dir.glob("*.profile.json"):
            try:
                profile = AgentProfile.from_json_file(profile_file)
                self.profiles[profile.agent_id] = profile
                count += 1
            except Exception as e:
                print(f"Warning: Failed to load {profile_file}: {e}")
        
        return count
    
    def get(self, agent_id: str) -> Optional[AgentProfile]:
        """获取指定 Agent Profile"""
        return self.profiles.get(agent_id)
    
    def get_pilot_agents(self) -> List[AgentProfile]:
        """获取所有 pilot agents"""
        return [p for p in self.profiles.values() if p.pilot]
    
    def get_by_role(self, role: str) -> List[AgentProfile]:
        """按角色获取 Agent Profiles"""
        return [p for p in self.profiles.values() if p.role == role]
    
    def register(self, profile: AgentProfile) -> None:
        """注册 Agent Profile"""
        self.profiles[profile.agent_id] = profile
        self._save_profile(profile)
    
    def _save_profile(self, profile: AgentProfile) -> None:
        """保存 Agent Profile 到文件"""
        profile_path = self.registry_dir / f"{profile.agent_id}.profile.json"
        profile.save_to_json_file(profile_path)
    
    def create_memory_space(self, agent_id: str) -> Path:
        """
        为 Agent 创建私有记忆空间
        
        Returns:
            记忆空间根路径
        """
        profile = self.get(agent_id)
        if not profile:
            raise ValueError(f"Agent {agent_id} not found")
        
        memory_root = profile.get_memory_root_path(self.project_root)
        memory_root.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        if profile.memory_config:
            (memory_root / profile.memory_config.long_term_memory_dir).mkdir(exist_ok=True)
        
        return memory_root
