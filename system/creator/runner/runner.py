"""
Runner — 运行区 Agent 实例管理

注册、查找、调用运行中的 Agent。
"""

from typing import Dict, Optional, Any
from system.models.agent import AgentDef


class Runner:
    """运行区管理器"""
    
    def __init__(self):
        self._agents: Dict[str, AgentDef] = {}
    
    def register(self, agent: AgentDef):
        """注册 Agent 到运行区"""
        agent.is_running = True
        self._agents[agent.name] = agent
    
    def unregister(self, name: str):
        """从运行区移除"""
        if name in self._agents:
            self._agents[name].is_running = False
            del self._agents[name]
    
    def get(self, name: str) -> Optional[AgentDef]:
        """获取运行中的 Agent"""
        return self._agents.get(name)
    
    def list_active(self) -> Dict[str, AgentDef]:
        """列出所有活跃 Agent"""
        return dict(self._agents)
    
    def call(self, name: str, input_data: Any = None) -> Any:
        """
        调用 Agent（未来扩展：实际调用 LLM + 注入 Skill/Tool）
        
        当前返回 Agent 的 Skill 和 Tool 描述信息。
        """
        agent = self._agents.get(name)
        if not agent:
            return f"Agent @{name} 不在运行中"
        
        return {
            "agent": agent.name,
            "description": agent.description,
            "skills": [s.name for s in agent.skills],
            "tools": [t.name for t in agent.tools],
            "skills_count": len(agent.skills),
            "tools_count": len(agent.tools)
        }
