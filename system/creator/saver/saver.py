"""
Saver — 将 Agent 保存到保存区并生成索引
"""

import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from system.models.agent import AgentDef, SkillDef, ToolDef, AgentSource


class Saver:
    """Agent 保存器"""
    
    def __init__(self, agent_dir: Path):
        self.agent_dir = agent_dir
        agent_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, agent: AgentDef) -> str:
        """
        保存 Agent 到保存区
        
        目录结构:
        workspace/agent/<name>/
            agent.md          # 原始定义
            agent.json        # 结构化定义
            skills/           # 分解的 Skill 文件
            tools/            # 分解的 Tool 文件
        """
        agent_path = self.agent_dir / agent.name
        agent_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 保存 agent.md
        if agent.raw_markdown:
            md_path = agent_path / "agent.md"
            md_path.write_text(agent.raw_markdown, encoding="utf-8")
        
        # 2. 保存 agent.json（结构化定义）
        json_path = agent_path / "agent.json"
        json_path.write_text(self._to_json(agent), encoding="utf-8")
        
        # 3. 保存 Skills
        skills_dir = agent_path / "skills"
        skills_dir.mkdir(exist_ok=True)
        for skill in agent.skills:
            skill_path = skills_dir / f"{skill.name}.md"
            skill_path.write_text(
                f"# {skill.name}\n\n{skill.instructions}\n\n> {skill.description}",
                encoding="utf-8"
            )
        
        # 4. 保存 Tools
        tools_dir = agent_path / "tools"
        tools_dir.mkdir(exist_ok=True)
        for tool in agent.tools:
            tool_path = tools_dir / f"{tool.name}.py"
            tool_path.write_text(tool.code, encoding="utf-8")
        
        agent.updated_at = datetime.now().isoformat()
        return str(agent_path)
    
    def load(self, name: str) -> Optional[AgentDef]:
        """从保存区加载 Agent"""
        agent_path = self.agent_dir / name
        json_path = agent_path / "agent.json"
        
        if not json_path.exists():
            return None
        
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            return self._from_json(data)
        except (json.JSONDecodeError, KeyError):
            return None
    
    def _to_json(self, agent: AgentDef) -> str:
        data = {
            "name": agent.name,
            "description": agent.description,
            "phase": agent.phase.value if hasattr(agent.phase, 'value') else agent.phase,
            "version": agent.version,
            "skills": [
                {
                    "name": s.name,
                    "description": s.description,
                    "instructions": s.instructions,
                    "priority": s.priority,
                    "enabled": s.enabled
                }
                for s in agent.skills
            ],
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "code": t.code,
                    "language": t.language,
                    "parameters": t.parameters,
                    "returns": t.returns,
                    "dependencies": t.dependencies
                }
                for t in agent.tools
            ],
            "source": {
                "type": agent.source.type if agent.source else "",
                "url": agent.source.url if agent.source else "",
                "path": agent.source.path if agent.source else ""
            } if agent.source else {},
            "created_at": agent.created_at,
            "updated_at": agent.updated_at,
            "is_active": agent.is_active,
            "extra": agent.extra
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _from_json(self, data: dict) -> AgentDef:
        agent = AgentDef(
            name=data["name"],
            description=data.get("description", ""),
            phase=data.get("phase", "saved"),
            version=data.get("version", "1.0.0"),
            skills=[
                SkillDef(**s)
                for s in data.get("skills", [])
            ],
            tools=[
                ToolDef(**t)
                for t in data.get("tools", [])
            ],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            is_active=data.get("is_active", False),
            extra=data.get("extra", {})
        )
        
        src = data.get("source", {})
        if src:
            agent.source = AgentSource(
                type=src.get("type", ""),
                url=src.get("url", ""),
                path=src.get("path", "")
            )
        
        return agent
