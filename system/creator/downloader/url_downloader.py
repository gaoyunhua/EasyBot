"""
URL 下载器 — 从 HTTP/HTTPS URL 获取 Agent 定义文件
"""

import os
import requests
from pathlib import Path
from typing import Tuple, List
from system.models.agent import AgentDef


class UrlDownloader:
    """从 URL 下载 agent.md"""
    
    def __init__(self, download_dir: Path):
        self.download_dir = download_dir
        download_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self, agent: AgentDef, url: str) -> Tuple[bool, List[str]]:
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            content = resp.text
        except requests.RequestException as e:
            return False, [f"下载失败: {e}"]
        
        # 保存到下载区
        agent_dir = self.download_dir / agent.name
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = agent_dir / "agent.md"
        filepath.write_text(content, encoding="utf-8")
        
        agent.raw_path = str(filepath)
        agent.raw_markdown = content
        return True, []
