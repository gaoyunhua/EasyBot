"""
GitHub 下载器 — 从 GitHub repo 获取 Agent 定义文件
"""

import os
import tempfile
from pathlib import Path
from typing import Tuple, List
from system.models.agent import AgentDef


class GithubDownloader:
    """从 GitHub 下载 agent.md"""
    
    def __init__(self, download_dir: Path):
        self.download_dir = download_dir
        download_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self, agent: AgentDef, repo: str, path: str = "") -> Tuple[bool, List[str]]:
        """
        从 GitHub 下载 agent.md
        
        Args:
            repo: "username/repo" 或完整 URL
            path: 仓库内的路径（可选）
        """
        # 清理 repo 格式
        repo = repo.replace("https://github.com/", "").replace("git@github.com:", "")
        repo = repo.rstrip("/")
        
        # 尝试多个可能的 URL 找到 agent.md
        urls_to_try = []
        base = f"https://raw.githubusercontent.com/{repo}/main"
        
        if path:
            urls_to_try.append(f"{base}/{path}")
            # 如果 path 是目录，尝试 agent.md
            if not path.endswith(".md"):
                urls_to_try.append(f"{base}/{path}/agent.md")
                urls_to_try.append(f"{base}/{path}/README.md")
        else:
            urls_to_try.append(f"{base}/agent.md")
            urls_to_try.append(f"{base}/README.md")
            # 也尝试 master 分支
            base_master = f"https://raw.githubusercontent.com/{repo}/master"
            urls_to_try.append(f"{base_master}/agent.md")
            urls_to_try.append(f"{base_master}/README.md")
        
        import requests
        
        content = None
        used_url = None
        for url in urls_to_try:
            try:
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200:
                    content = resp.text
                    used_url = url
                    break
            except requests.RequestException:
                continue
        
        if content is None:
            return False, [f"无法从 GitHub 仓库 {repo} 获取 agent.md（尝试了 {len(urls_to_try)} 个 URL）"]
        
        # 保存到下载区
        agent_dir = self.download_dir / agent.name
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = agent_dir / "agent.md"
        filepath.write_text(content, encoding="utf-8")
        
        agent.raw_path = str(filepath)
        agent.raw_markdown = content
        return True, []
