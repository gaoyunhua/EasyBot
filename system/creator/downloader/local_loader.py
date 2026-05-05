"""
本地加载器 — 从本地文件加载 Agent 定义
"""

import os
from pathlib import Path
from typing import Tuple, List
from system.models.agent import AgentDef


class LocalLoader:
    """从本地文件加载 agent.md"""
    
    def __init__(self, download_dir: Path):
        self.download_dir = download_dir
        download_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self, agent: AgentDef, filepath: str) -> Tuple[bool, List[str]]:
        path = Path(filepath)
        
        if not path.exists():
            return False, [f"文件不存在: {filepath}"]
        
        if path.suffix not in (".md", ".txt"):
            return False, [f"不支持的文件格式: {path.suffix}，需要 .md"]
        
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return False, [f"读取文件失败: {e}"]
        
        if not content.strip():
            return False, ["文件为空"]
        
        # 自动从文件名提取名称：默认用父目录名（如 calculator/agent.md → calculator）
        if not agent.name or agent.name == "unnamed_agent":
            parent_name = path.parent.name
            agent.name = parent_name if parent_name != "." else path.stem
        
        # 复制到下载区
        agent_dir = self.download_dir / agent.name
        agent_dir.mkdir(parents=True, exist_ok=True)
        dest_path = agent_dir / "agent.md"
        dest_path.write_text(content, encoding="utf-8")
        
        agent.raw_path = str(dest_path)
        agent.raw_markdown = content
        return True, []
