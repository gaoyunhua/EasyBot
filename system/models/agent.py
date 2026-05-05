"""
EasyBot 数据模型 — Agent、Skill、Tool 定义

所有模块共享的核心数据结构。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class AgentPhase(str, Enum):
    """Agent 生命周期四阶段"""
    DOWNLOAD = "downloaded"       # 下载区
    IMPORTING = "importing"       # 调试导入区
    SAVED = "saved"              # 保存区
    ACTIVE = "active"            # 运行区


class ImportStatus(str, Enum):
    """调试导入状态"""
    PENDING = "pending"           # 等待导入
    PARSING = "parsing"           # 解析中
    VALIDATING = "validating"     # 验证中
    TESTING = "testing"           # 测试中
    PASSED = "passed"             # 通过
    FAILED = "failed"             # 失败
    ERROR = "error"               # 异常


@dataclass
class ToolDef:
    """工具定义 — 可执行函数"""
    name: str
    description: str
    code: str                    # 代码内容
    language: str = "python"
    parameters: Dict[str, str] = field(default_factory=dict)  # 参数名→描述
    returns: str = ""
    dependencies: List[str] = field(default_factory=list)


@dataclass
class SkillDef:
    """技能定义 — 注入 LLM system prompt 的能力描述"""
    name: str
    description: str             # 简短描述
    instructions: str = ""       # 详细的指令文本（注入 prompt 用）
    priority: int = 5
    enabled: bool = True


@dataclass
class AgentSource:
    """来源信息"""
    type: str                    # "github", "url", "local", "manual"
    url: str = ""
    path: str = ""
    version: str = ""


@dataclass
class AgentDef:
    """完整的 Agent 定义"""
    name: str
    description: str = ""
    phase: AgentPhase = AgentPhase.DOWNLOAD
    source: Optional[AgentSource] = None
    import_status: ImportStatus = ImportStatus.PENDING
    import_errors: List[str] = field(default_factory=list)
    
    # 解析后的内容
    skills: List[SkillDef] = field(default_factory=list)
    tools: List[ToolDef] = field(default_factory=list)
    
    # 原始内容
    raw_markdown: str = ""
    raw_path: str = ""           # agent.md 文件路径（保存区/运行区）
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"
    
    # 运行状态
    is_running: bool = False
    is_active: bool = False
    last_called: str = ""

    # 扩展信息（Examples, Templates, Rules, Workflows, Metadata 等）
    extra: Dict[str, str] = field(default_factory=dict)


@dataclass
class TestResult:
    """测试结果"""
    passed: bool = False
    skill_results: Dict[str, bool] = field(default_factory=dict)
    tool_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
