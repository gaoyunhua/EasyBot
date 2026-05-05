"""
EasyBot System Package

全局配置变量：
- WORKSPACE: 工作区根目录路径
- MODEL_PROVIDER: 模型提供 Agent 实例
- CONNECTOR: 连接器 Agent 实例
- CHARTER: Agent 章程/角色定义
"""

from pathlib import Path
from typing import Optional
from system.models.agent import AgentDef

WORKSPACE: Path = None

MODEL_PROVIDER: Optional[AgentDef] = None

CONNECTOR: Optional[AgentDef] = None

CHARTER: dict = None


def init_globals(
    workspace: Path = None,
    model_provider: AgentDef = None,
    connector: AgentDef = None,
    charter: dict = None
):
    """
    初始化全局变量

    Args:
        workspace: 工作区根目录路径
        model_provider: 模型提供 Agent 实例
        connector: 连接器 Agent 实例
        charter: Agent 章程/角色定义字典
    """
    global WORKSPACE, MODEL_PROVIDER, CONNECTOR, CHARTER

    if workspace is not None:
        WORKSPACE = Path(workspace) if not isinstance(workspace, Path) else workspace

    if model_provider is not None:
        MODEL_PROVIDER = model_provider
        
    if connector is not None:
        CONNECTOR = connector
        
    if charter is not None:
        CHARTER = charter


def get_workspace() -> Path:
    """获取工作区路径"""
    return WORKSPACE


def get_model_provider() -> Optional[AgentDef]:
    """获取模型提供 Agent"""
    return MODEL_PROVIDER


def get_connector() -> Optional[AgentDef]:
    """获取连接器 Agent"""
    return CONNECTOR


def get_charter() -> dict:
    """获取 Agent 章程"""
    return CHARTER
