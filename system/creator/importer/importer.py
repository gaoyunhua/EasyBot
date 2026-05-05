"""
Importer — 解析 Agent 的 Markdown 定义

把 agent.md 解析成结构化的 SkillDef 和 ToolDef。

支持的格式（新旧格式兼容）：
  新格式: ## Description, ## Actions (Skills), ## Tools
  旧格式: ## Overview → Description, ## Actions → Skills
  扩展:   ## Examples, ## Templates, ## Rules, ## Workflows, ## Metadata
"""

import re
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
from system.models.agent import AgentDef, SkillDef, ToolDef, AgentSource


class Importer:
    """
    解析 Agent 的 Markdown 定义
    """

    # 旧格式 → 新格式的映射
    SECTION_ALIASES = {
        "overview": "description",
        "description": "description",
        "actions (skills)": "actions",
        "actions": "actions",
        "tasks": "actions",
        "skill": "actions",
    }

    # 直接保留的扩展 section
    EXTRA_SECTIONS = {"examples", "templates", "rules", "workflows", "metadata", "config", "dependencies"}

    # 需要忽略的 section（旧格式里的无用信息）
    IGNORE_SECTIONS = {"usage", "files", "license", "requirements"}

    def parse(self, agent: AgentDef) -> Tuple[Dict[str, Any], List[str]]:
        """
        解析 agent.raw_markdown 或 agent.raw_path

        Returns:
            (dict_with_skills_tools, list_of_errors)
        """
        content = agent.raw_markdown
        if not content and agent.raw_path:
            path = Path(agent.raw_path)
            if path.exists():
                content = path.read_text(encoding="utf-8")

        if not content:
            return {}, ["无 Markdown 内容可解析"]

        errors = []
        result = {
            "skills": [],
            "tools": [],
            "description": "",
            "raw_markdown": content,
            "extra": {},  # 扩展 section: examples, templates, rules, workflows, metadata
        }

        lines = content.split("\n")
        current_section = None
        tool_code_buffer = []
        collecting_tool = False
        in_sub_heading = False  # ### 子标题中，跳过内容行

        # 多行收集
        section_buffer = []

        # 扫描文件顶部（第一个 ## 之前）的 **Description** 行
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("## "):
                break
            if "**Description**" in stripped:
                desc_line = re.sub(r'^.*\*\*Description\*\*:\s*', '', stripped).strip()
                if desc_line:
                    result["description"] = desc_line

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 检测标题 (##)
            heading_match = re.match(r'^##\s+(.+)$', stripped)
            if heading_match:
                # 结束上一个工具的代码收集
                if collecting_tool and tool_code_buffer:
                    self._finalize_tool(result, tool_code_buffer)
                    tool_code_buffer = []
                    collecting_tool = False

                # 处理上一个 section 的缓冲内容
                self._flush_section_buffer(result, current_section, section_buffer)
                section_buffer = []

                heading = heading_match.group(1).strip()
                heading_lower = heading.lower()

                # 映射
                resolved = self._resolve_section(heading_lower, result, errors)
                if resolved:
                    current_section = resolved
                elif heading_lower in self.EXTRA_SECTIONS:
                    current_section = heading_lower
                elif heading_lower in self.IGNORE_SECTIONS:
                    current_section = "ignore"
                else:
                    current_section = None

                continue

            # 检测三级标题 (###)
            sub_heading_match = re.match(r'^###\s+(.+)$', stripped)
            if sub_heading_match and current_section == "actions":
                # ### 子标题: 结束上一个，开始一个新的
                in_sub_heading = True
                self._flush_section_buffer(result, current_section, section_buffer)
                section_buffer = []
                sub_text = sub_heading_match.group(1).strip()
                sub_text = re.sub(r'^\d+[\.\)]\s*', '', sub_text)
                skill = SkillDef(name=sub_text, description=sub_text)
                result["skills"].append(skill)
                continue

            # 在 actions section 的 ### 子标题范围内，跳过所有非 ###/## 内容行
            if in_sub_heading:
                # 遇到另一个 ### 会由上面的逻辑处理，然后继续
                # 遇到 ## 会由 section 检测处理
                if stripped.startswith("## "):
                    in_sub_heading = False  # 新的 section，退出子标题
                    # 不 continue，让下面 section 检测处理
                else:
                    continue  # 跳过子标题内的所有内容

            # 内容解析
            if current_section == "description":
                if stripped.startswith("**Description**") or stripped.startswith("- **Description**"):
                    desc_line = re.sub(r'^-?\s*\*\*Description\*\*:\s*', '', stripped).strip()
                    if desc_line:
                        section_buffer.append(desc_line)
                elif stripped and not stripped.startswith("#") and not stripped.startswith("-") and not stripped.startswith("*") and not stripped.startswith("```") and not stripped.startswith("|") and not stripped.startswith("---"):
                    section_buffer.append(stripped)

            elif current_section == "actions":
                # ### 子标题已经在上面处理了，这里处理 - 列表
                if self._is_skill_line(stripped):
                    section_buffer.append(stripped)
                elif stripped and not stripped.startswith("#") and not stripped.startswith("```") and not stripped.startswith("**"):
                    # 上一行 skill 的延续描述
                    if stripped.startswith("`") or stripped.startswith("-"):
                        # ``` 内的参数/example 行，不需要延续
                        pass
                    elif section_buffer and not stripped.startswith("-") and not stripped.startswith("*"):
                        section_buffer[-1] = section_buffer[-1] + " " + stripped

            elif current_section == "tools":
                # 检测代码块开始
                if stripped.startswith("```"):
                    if not collecting_tool:
                        # 开始收集
                        collecting_tool = True
                        tool_code_buffer = []
                    else:
                        # 结束收集
                        self._finalize_tool(result, tool_code_buffer)
                        tool_code_buffer = []
                        collecting_tool = False
                    continue

                if collecting_tool:
                    tool_code_buffer.append(line)

            elif current_section in self.EXTRA_SECTIONS:
                if stripped and not stripped.startswith("#"):
                    section_buffer.append(stripped)

            # ignore 的 section 跳过

        # 清理缓冲区
        if collecting_tool and tool_code_buffer:
            self._finalize_tool(result, tool_code_buffer)
        self._flush_section_buffer(result, current_section, section_buffer)

        # 清理多余的 import 行（多个 def 时每个都带了 import）
        self._dedup_imports(result)

        # 尝试简化模式兜底
        if not result["skills"] and not result["tools"] and not result["description"]:
            alt_result, alt_errors = self._parse_simple(content)
            if alt_result.get("skills") or alt_result.get("tools") or alt_result.get("description"):
                result = alt_result
                return result, alt_errors

        return result, errors

    def _resolve_section(self, heading_lower: str, result: dict, errors: list) -> Optional[str]:
        """解析 section 名称，支持别名映射"""
        # 精确匹配
        mapped = self.SECTION_ALIASES.get(heading_lower)
        if mapped:
            return mapped

        # 模糊匹配: "actions (skills)" → actions
        for alias, target in self.SECTION_ALIASES.items():
            if alias in heading_lower or heading_lower in alias:
                return target

        # 模糊匹配 tool
        if "tool" in heading_lower:
            return "tools"

        return None

    def _flush_section_buffer(self, result: dict, section: Optional[str], buffer: list):
        """把收集的缓冲内容刷到 result 中"""
        if not buffer or not section:
            return

        if section == "description":
            result["description"] = "\n".join(buffer).strip()

        elif section == "actions":
            for line in buffer:
                if self._is_skill_line(line):
                    skill = self._parse_skill_line(line)
                    if skill and skill.name:
                        result["skills"].append(skill)

        elif section in self.EXTRA_SECTIONS:
            text = "\n".join(buffer).strip()
            if text:
                result.setdefault("extra", {})[section] = text

        buffer.clear()

    def _is_skill_line(self, line: str) -> bool:
        """检测是否为 Skill 列表项"""
        stripped = line.strip()
        # 排除 **bold** 格式的元数据行 (Parameters, Example, Description 等)
        if stripped.startswith("**") and stripped.endswith("**"):
            return False
        if stripped.startswith("-") or stripped.startswith("*"):
            if "```" in stripped:
                return False
            if "def " in stripped or "import " in stripped:
                return False
            # 排除 `- **Key**: Value` 这类元数据行
            if re.match(r'^- \*\*.+\*\*:', stripped):
                return False
            # 排除参数行: `- `param`: ...`
            if "`" in stripped:
                return False
            return True
        if re.match(r'^\d+[\.\)]\s', stripped):
            return True
        return False

    def _parse_skill_line(self, line: str) -> Optional[SkillDef]:
        """解析一行 Skill 定义，支持多行累积"""
        stripped = line.strip().lstrip("-* ")

        # 去掉数字序号: "1. Plan Project" → "Plan Project"
        stripped = re.sub(r'^\d+[\.\)]\s*', '', stripped).strip()

        name = None
        desc = stripped

        if ":" in stripped:
            parts = stripped.split(":", 1)
            name = parts[0].strip()
            desc = parts[1].strip()
        elif "—" in stripped:
            parts = stripped.split("—", 1)
            name = parts[0].strip()
            desc = parts[1].strip()
        elif " - " in stripped:
            parts = stripped.split(" - ", 1)
            name = parts[0].strip()
            desc = parts[1].strip()

        if not name:
            # 无分隔符: 用该行作为 skill name，描述自动生成
            name = stripped
            if not desc:
                desc = name

        return SkillDef(
            name=name.lower().replace(" ", "_"),
            description=desc,
            instructions=f"{desc}"
        )

    def _finalize_tool(self, result: dict, code_buffer: list):
        """将代码块中的多个工具定义转为 ToolDef"""
        code = "\n".join(code_buffer).strip()
        if not code:
            return

        # 按 def 分割代码
        parts = re.split(r'(^def\s)', code, flags=re.MULTILINE)

        if len(parts) <= 1:
            self._parse_single_def(result, code)
            return

        # 多个 def — 共享 imports
        imports = parts[0]
        for i in range(1, len(parts), 2):
            func_code = parts[i] + parts[i + 1] if i + 1 < len(parts) else parts[i]
            full_code = (imports + "\n" + func_code).strip()
            self._parse_single_def(result, full_code, imports)

    def _parse_single_def(self, result: dict, code: str, imports: str = ""):
        """解析单函数定义"""
        func_match = re.search(r'def\s+(\w+)\s*\(([^)]*)\)\s*->?\s*([^:]*)\s*:', code)
        if not func_match:
            func_match = re.search(r'def\s+(\w+)\s*\(([^)]*)\)\s*:', code)

        if not func_match:
            return

        tool_name = func_match.group(1)
        params_str = func_match.group(2)
        returns = func_match.group(3).strip() if len(func_match.groups()) >= 3 else ""

        # 提取参数
        params = {}
        if params_str.strip():
            for p in params_str.split(","):
                p = p.strip()
                if ":" in p:
                    p_name, p_type = p.split(":", 1)
                    params[p_name.strip()] = p_type.strip()
                elif p:
                    params[p] = "any"

        # 提取 docstring 作为描述
        doc_match = re.search(r'"""(.+?)"""', code, re.DOTALL)
        docstring = doc_match.group(1).strip().split("\n")[0] if doc_match else f"Tool: {tool_name}"

        result["tools"].append(ToolDef(
            name=tool_name,
            description=docstring,
            code=code,
            parameters=params,
            returns=returns
        ))

    def _dedup_imports(self, result: dict):
        """多个 def 工具共享 imports 时，去重多余的行"""
        if len(result["tools"]) < 2:
            return

        # 找到所有工具的代码，去重每个文件顶部的 import 行
        seen_imports = set()
        for tool in result["tools"]:
            lines = tool.code.split("\n")
            clean_lines = []
            for line in lines:
                if line.strip().startswith(("import ", "from ")):
                    key = line.strip()
                    if key not in seen_imports:
                        seen_imports.add(key)
                        clean_lines.append(line)
                else:
                    clean_lines.append(line)
            tool.code = "\n".join(clean_lines)

    def _parse_simple(self, content: str) -> Tuple[Dict[str, Any], List[str]]:
        """简化模式 — 没有任何标题标记时尝试理解内容"""
        result = {
            "skills": [],
            "tools": [],
            "description": "",
            "raw_markdown": content,
            "extra": {},
        }
        errors = []

        lines = content.split("\n")
        found_desc = False

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                if stripped.startswith("# ") and not found_desc:
                    result["description"] = stripped[2:].strip()
                    found_desc = True
                continue

            if not found_desc and len(stripped) < 200:
                result["description"] = stripped[:100]
                found_desc = True

            if stripped.startswith("```"):
                continue

        if not result["description"]:
            errors.append("未找到描述")

        return result, errors
