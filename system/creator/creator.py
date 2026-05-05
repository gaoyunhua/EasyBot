"""
Agent Creator — 四区流水线管理

管理 Agent 从下载到运行的完整生命周期：
  下载区 → 调试导入区 → 保存区 → 运行区
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from system.models.agent import (
    AgentDef, AgentPhase, ImportStatus, AgentSource,
    SkillDef, ToolDef, TestResult
)
from system import WORKSPACE as GLOBAL_WORKSPACE


def _get_workspace_dir():
    """获取工作区目录，优先使用全局变量 WORKSPACE"""
    if GLOBAL_WORKSPACE is not None:
        return GLOBAL_WORKSPACE
    return Path(__file__).resolve().parent.parent.parent / "workspace"

def _get_project_dir():
    """获取项目根目录"""
    return Path(__file__).resolve().parent.parent.parent


PROJECT_DIR = _get_project_dir()
WORKSPACE_DIR = _get_workspace_dir()
DOWNLOAD_DIR = WORKSPACE_DIR / "downloaded"
AGENT_DIR = WORKSPACE_DIR / "agent"
INDEX_FILE = WORKSPACE_DIR / "agent_index.json"


class AgentCreator:
    """
    Agent Creator — 四区流水线

    使用方式：
    creator = AgentCreator()
    agent, errors = creator.download_from_url("https://...")
    agent, errors = creator.import_agent(agent)
    result = creator.test_agent(agent)
    agent = creator.save_agent(agent)
    agent = creator.activate_agent(agent)
    """

    def __init__(self):
        self._index = self._load_index()
        self._importer = None
        self._tester = None
        self._saver = None
        self._runner = None

    # ─── 1. 下载区 ───

    def download_from_url(self, url: str, name: str = "") -> tuple:
        """从 URL 下载 Agent 定义到下载区"""
        agent = AgentDef(
            name=name or self._extract_name_from_url(url),
            phase=AgentPhase.DOWNLOAD,
            source=AgentSource(type="url", url=url)
        )

        from system.creator.downloader.url_downloader import UrlDownloader
        downloader = UrlDownloader(DOWNLOAD_DIR)
        success, errors = downloader.download(agent, url)

        if not success:
            agent.import_status = ImportStatus.ERROR
            agent.import_errors = errors
            return agent, errors

        agent.import_status = ImportStatus.PENDING
        return agent, []

    def download_from_github(self, repo: str, path: str = "", name: str = "") -> tuple:
        """从 GitHub 下载 Agent"""
        from system.creator.downloader.github_downloader import GithubDownloader
        return self._download_with(
            GithubDownloader(DOWNLOAD_DIR),
            name or repo.split("/")[-1],
            AgentSource(type="github", url=f"https://github.com/{repo}"),
            repo, path
        )

    def download_from_local(self, filepath: str, name: str = "") -> tuple:
        """从本地文件导入"""
        p = Path(filepath)
        auto_name = p.parent.name if p.parent.name and p.parent.name != "." else p.stem
        agent = AgentDef(
            name=name or auto_name,
            phase=AgentPhase.DOWNLOAD,
            source=AgentSource(type="local", path=filepath)
        )

        from system.creator.downloader.local_loader import LocalLoader
        loader = LocalLoader(DOWNLOAD_DIR)
        success, errors = loader.load(agent, filepath)

        if not success:
            agent.import_status = ImportStatus.ERROR
            agent.import_errors = errors
            return agent, errors

        agent.import_status = ImportStatus.PENDING
        return agent, []

    def _download_with(self, downloader, name, source, *args) -> tuple:
        agent = AgentDef(name=name, phase=AgentPhase.DOWNLOAD, source=source)
        success, errors = downloader.download(agent, *args)
        if not success:
            agent.import_status = ImportStatus.ERROR
            agent.import_errors = errors
            return agent, errors
        agent.import_status = ImportStatus.PENDING
        return agent, []

    def _extract_name_from_url(self, url: str) -> str:
        import re
        match = re.search(r'/([^/]+?)(?:\.md)?$', url)
        return match.group(1) if match else "unnamed_agent"

    # ─── 2. 调试导入区 ───

    def import_agent(self, agent: AgentDef) -> tuple:
        """解析、导入并验证 Agent 定义"""
        agent.phase = AgentPhase.IMPORTING
        agent.import_status = ImportStatus.PARSING

        if self._importer is None:
            from system.creator.importer.importer import Importer
            self._importer = Importer()

        parsed, errors = self._importer.parse(agent)
        if errors:
            agent.import_status = ImportStatus.FAILED
            agent.import_errors = errors
            return agent, errors

        agent.skills = parsed.get("skills", [])
        agent.tools = parsed.get("tools", [])
        agent.description = parsed.get("description", agent.description)
        agent.raw_markdown = parsed.get("raw_markdown", agent.raw_markdown)
        agent.extra = parsed.get("extra", {})

        agent.import_status = ImportStatus.PASSED
        return agent, []

    # ─── 3. 调试区测试 ───

    def test_agent(self, agent: AgentDef, auto_fix: bool = False) -> TestResult:
        """测试 Agent 的 Skill 和 Tool"""
        agent.import_status = ImportStatus.TESTING

        if self._tester is None:
            from system.tester.tester import AgentTester
            self._tester = AgentTester()

        result = self._tester.test(agent)
        agent.import_status = ImportStatus.PASSED if result.passed else ImportStatus.FAILED
        return result

    # ─── 4. 保存区 ───

    def save_agent(self, agent: AgentDef) -> AgentDef:
        """保存 Agent 到保存区"""
        agent.phase = AgentPhase.SAVED

        if self._saver is None:
            from system.creator.saver.saver import Saver
            self._saver = Saver(AGENT_DIR)

        saved_path = self._saver.save(agent)
        agent.raw_path = str(saved_path)

        self._index[agent.name] = {
            "name": agent.name,
            "description": agent.description,
            "phase": agent.phase.value,
            "path": str(saved_path),
            "skills_count": len(agent.skills),
            "tools_count": len(agent.tools),
            "version": agent.version,
            "updated_at": agent.updated_at
        }
        self._save_index()

        return agent

    # ─── 5. 运行区 ───

    def activate_agent(self, agent: AgentDef) -> AgentDef:
        """激活 Agent 到运行区"""
        agent.phase = AgentPhase.ACTIVE
        agent.is_running = True
        agent.is_active = True

        if self._runner is None:
            from system.creator.runner.runner import Runner
            self._runner = Runner()

        self._runner.register(agent)

        if agent.name in self._index:
            self._index[agent.name]["phase"] = AgentPhase.ACTIVE.value
            self._save_index()

        return agent

    def deactivate_agent(self, agent: AgentDef) -> AgentDef:
        """停用 Agent"""
        agent.phase = AgentPhase.SAVED
        agent.is_running = False
        if self._runner:
            self._runner.unregister(agent.name)

        if agent.name in self._index:
            self._index[agent.name]["phase"] = AgentPhase.SAVED.value
            self._save_index()

        return agent

    # ─── 创建 Agent ───

    def create_agent(self, name: str, requirement: str) -> tuple:
        """根据需求创建新的 Agent"""
        agent = AgentDef(
            name=name,
            description=requirement,
            phase=AgentPhase.SAVED,
            skills=[],
            tools=[]
        )

        agent_path = AGENT_DIR / name
        agent_path.mkdir(parents=True, exist_ok=True)

        markdown_content = f"""# {name}

## Description
{requirement}

## Skills
- Basic skill: {requirement}

## Tools
"""
        markdown_path = agent_path / "agent.md"
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        agent.raw_path = str(markdown_path)
        agent.raw_markdown = markdown_content

        self._index[agent.name] = {
            "name": agent.name,
            "description": agent.description,
            "phase": agent.phase.value,
            "path": str(markdown_path),
            "skills_count": len(agent.skills),
            "tools_count": len(agent.tools),
            "version": agent.version,
            "updated_at": agent.updated_at
        }
        self._save_index()

        return agent, []

    # ─── 一站式流水线 ───

    def full_pipeline_from_local(self, filepath: str, name: str = "",
                                  auto_activate: bool = True) -> tuple:
        """一键导入：本地文件 → 完成全部四阶段"""
        agent, errors = self.download_from_local(filepath, name)
        if errors:
            return agent, errors, None

        agent, errors = self.import_agent(agent)
        if errors:
            return agent, errors, None

        result = self.test_agent(agent)
        if not result.passed:
            return agent, result.errors, result

        agent = self.save_agent(agent)

        if auto_activate:
            agent = self.activate_agent(agent)

        return agent, [], result

    def full_pipeline_from_url(self, url: str, name: str = "",
                                auto_activate: bool = True) -> tuple:
        """一键导入：URL → 完成全部四阶段"""
        agent, errors = self.download_from_url(url, name)
        if errors:
            return agent, errors, None
        return self._continue_pipeline(agent, auto_activate)

    def full_pipeline_from_github(self, repo: str, path: str = "",
                                   name: str = "",
                                   auto_activate: bool = True) -> tuple:
        """一键导入：GitHub → 完成全部四阶段"""
        agent, errors = self.download_from_github(repo, path, name)
        if errors:
            return agent, errors, None
        return self._continue_pipeline(agent, auto_activate)

    def _continue_pipeline(self, agent, auto_activate):
        agent, errors = self.import_agent(agent)
        if errors:
            return agent, errors, None

        result = self.test_agent(agent)
        if not result.passed:
            return agent, result.errors, result

        agent = self.save_agent(agent)
        if auto_activate:
            agent = self.activate_agent(agent)

        return agent, [], result

    # ─── 辅助 ───

    def list_agents(self, phase: Optional[AgentPhase] = None) -> List[dict]:
        """列出 Agent（通过索引）"""
        if phase:
            return [info for info in self._index.values()
                    if info.get("phase") == phase.value]
        return list(self._index.values())

    def get_agent(self, name: str) -> Optional[AgentDef]:
        """从保存区加载 Agent"""
        info = self._index.get(name)
        if not info:
            return None

        from system.creator.saver.saver import Saver
        saver = Saver(AGENT_DIR)
        return saver.load(name)

    def _load_index(self) -> dict:
        if INDEX_FILE.exists():
            try:
                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_index(self):
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(self._index, f, ensure_ascii=False, indent=2)
