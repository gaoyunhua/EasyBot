"""
Agent Caller — 运行区 Agent 实例化

职责：
1. 从保存区/运行区读取 Agent 定义
2. 注册 Skill 描述 → 注入 LLM system prompt
3. 注册 Tool 函数 → 供 LLM function call
4. 提供统一调用接口（含日志、超时、重试、格式化输出）
"""

import importlib.util
import sys
import inspect
import time
import functools
import traceback
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from system.models.agent import AgentDef, SkillDef, ToolDef


@dataclass
class ToolCallRecord:
    """一次工具调用的完整记录"""
    tool_name: str
    agent_name: str
    arguments: Dict[str, Any]
    result: Any = None
    error: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    success: bool = False

    @property
    def formatted_duration(self) -> str:
        if self.duration_ms < 1000:
            return f"{self.duration_ms:.0f}ms"
        return f"{self.duration_ms/1000:.2f}s"


class AgentCaller:
    """
    Agent 调用器

    把保存的 Agent 变成可调用的"微 agent"：
    - Skills → LLM system prompt 注入
    - Tools → Python 函数注册
    """
    
    def __init__(self, max_retries: int = 2, timeout: int = 30):
        self._registry: Dict[str, AgentDef] = {}
        self._tool_functions: Dict[str, Dict[str, Callable]] = {}  # agent_name → {tool_name: func}
        self._call_log: Dict[str, List[ToolCallRecord]] = {}  # agent_name → [records]
        self._max_retries = max_retries
        self._timeout = timeout
        self._global_log: List[ToolCallRecord] = []  # 全局日志
    
    # ─── 注册 ───
    
    def register(self, agent: AgentDef):
        """注册 Agent，加载其 Tools 为可调用函数"""
        self._registry[agent.name] = agent
        self._load_tools(agent)
        if agent.name not in self._call_log:
            self._call_log[agent.name] = []
    
    def unregister(self, name: str):
        if name in self._registry:
            del self._registry[name]
        if name in self._tool_functions:
            del self._tool_functions[name]
        if name in self._call_log:
            del self._call_log[name]
    
    def _load_tools(self, agent: AgentDef):
        """加载 Agent 的 Tools 为 Python 可调用函数"""
        self._tool_functions[agent.name] = {}
        
        for tool in agent.tools:
            try:
                namespace = {}
                code_obj = compile(tool.code, f"<{agent.name}:{tool.name}>", "exec")
                exec(code_obj, namespace)
                
                func = namespace.get(tool.name)
                if func and callable(func):
                    self._tool_functions[agent.name][tool.name] = func
            except Exception as e:
                pass  # 不中断，让调用时再报错
    
    # ─── 查询 ───
    
    def get_system_prompt(self, agent_name: str) -> str:
        """生成注入 LLM 的 system prompt（Skills 描述）"""
        agent = self._registry.get(agent_name)
        if not agent:
            return ""
        
        lines = [f"# {agent.name}", "", agent.description, ""]
        
        if agent.skills:
            lines.append("## 你的能力")
            for skill in agent.skills:
                lines.append(f"- **{skill.name}**: {skill.description}")
                if skill.instructions:
                    lines.append(f"  {skill.instructions}")
            lines.append("")
        
        if agent.tools:
            lines.append("## 可用工具")
            for tool in agent.tools:
                params_desc = ", ".join(f"{k}: {v}" for k, v in tool.parameters.items())
                lines.append(f"- **{tool.name}({params_desc})**: {tool.description}")
            lines.append("")
        
        # Extra 内容
        if agent.extra:
            extra_sections = []
            for key, value in agent.extra.items():
                if value.strip():
                    extra_sections.append(f"## {key}\n{value}")
            if extra_sections:
                lines.append("---")
                lines.extend(extra_sections)
                lines.append("")
        
        return "\n".join(lines)
    
    def get_tool_definitions(self, agent_name: str) -> List[Dict[str, Any]]:
        """获取 Tools 的 JSON 定义（用于 function calling）"""
        agent = self._registry.get(agent_name)
        if not agent:
            return []
        
        definitions = []
        for tool in agent.tools:
            func = self._get_tool_function(agent_name, tool.name)
            if func is None:
                continue
            
            # 自动推导参数
            sig = inspect.signature(func)
            params = {
                name: {
                    "type": self._infer_type(param.annotation),
                    "description": tool.parameters.get(name, f"Parameter {name}")
                }
                for name, param in sig.parameters.items()
                if name != "self"
            }
            
            definitions.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": params,
                        "required": list(params.keys())
                    }
                }
            })
        
        return definitions
    
    def _get_tool_function(self, agent_name: str, tool_name: str) -> Optional[Callable]:
        return self._tool_functions.get(agent_name, {}).get(tool_name)
    
    # ─── 调用（增强版：日志 + 超时 + 重试）───
    
    def call_tool(self, agent_name: str, tool_name: str, **kwargs) -> Any:
        """
        调用 Agent 的 Tool 函数（带日志、超时、重试）
        """
        func = self._get_tool_function(agent_name, tool_name)
        if func is None:
            raise ValueError(f"Agent @{agent_name} 没有 Tool: {tool_name}")
        
        last_error = None
        
        for attempt in range(self._max_retries + 1):
            record = ToolCallRecord(
                tool_name=tool_name,
                agent_name=agent_name,
                arguments=kwargs,
                start_time=time.time()
            )
            
            try:
                # 带超时调用
                result = self._call_with_timeout(func, kwargs, self._timeout)
                record.result = result
                record.success = True
                record.end_time = time.time()
                record.duration_ms = (record.end_time - record.start_time) * 1000
                
                # 记录日志
                self._log_call(record)
                
                return self._format_result(result)
                
            except Exception as e:
                last_error = e
                record.error = str(e)
                record.success = False
                record.end_time = time.time()
                record.duration_ms = (record.end_time - record.start_time) * 1000
                
                self._log_call(record)
                
                if attempt < self._max_retries:
                    continue  # 重试
                else:
                    raise RuntimeError(
                        f"Tool @{agent_name}.{tool_name} 调用失败 "
                        f"(重试{self._max_retries}次): {e}"
                    ) from e
    
    def _call_with_timeout(self, func: Callable, kwargs: Dict, timeout: int) -> Any:
        """带超时调用（Python 纯实现）"""
        # 检查是否有 timeout 参数
        sig = inspect.signature(func)
        has_timeout_param = "timeout" in sig.parameters
        
        if has_timeout_param:
            kwargs = {**kwargs, "timeout": timeout}
        
        # 调用
        return func(**kwargs)
    
    def _format_result(self, result: Any) -> Any:
        """格式化工具调用结果"""
        if result is None:
            return "✅ 执行成功"
        if isinstance(result, (str, int, float, bool)):
            return result
        if isinstance(result, (list, tuple)):
            if len(result) == 0:
                return "[]"
            # 格式化列表
            formatted = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(result))
            return f"[\n{formatted}\n]"
        if isinstance(result, dict):
            if len(result) == 0:
                return "{}"
            # 格式化字典
            formatted = "\n".join(f"  {k}: {v}" for k, v in result.items())
            return f"{{\n{formatted}\n}}"
        return str(result)
    
    # ─── 日志 ───
    
    def _log_call(self, record: ToolCallRecord):
        """记录工具调用"""
        agent_log = self._call_log.setdefault(record.agent_name, [])
        agent_log.append(record)
        self._global_log.append(record)
        # 限制日志条数
        if len(agent_log) > 1000:
            agent_log.pop(0)
        if len(self._global_log) > 10000:
            self._global_log.pop(0)
    
    def get_call_log(self, agent_name: Optional[str] = None, 
                     limit: int = 20) -> List[ToolCallRecord]:
        """获取调用日志"""
        if agent_name:
            logs = self._call_log.get(agent_name, [])
        else:
            logs = self._global_log
        
        return logs[-limit:]
    
    def print_call_log(self, agent_name: Optional[str] = None, limit: int = 10):
        """打印调用日志（终端友好格式）"""
        logs = self.get_call_log(agent_name, limit)
        if not logs:
            print("📭 暂无调用记录")
            return
        
        print(f"📋 调用日志 ({'全局' if not agent_name else f'@{agent_name}'}):\n")
        for i, rec in enumerate(reversed(logs), 1):
            status = "✅" if rec.success else "❌"
            dur = rec.formatted_duration
            print(f"  {status} #{i} {rec.agent_name}.{rec.tool_name}() — {dur}")
            if rec.arguments:
                args_str = ", ".join(f"{k}={v}" for k, v in rec.arguments.items())
                print(f"      参数: {args_str}")
            if rec.success:
                result_str = str(rec.result)[:80]
                print(f"      结果: {result_str}")
            if rec.error:
                print(f"      错误: {rec.error}")
            print()
    
    # ─── 原兼容接口 ───
    
    def call_agent(self, agent_name: str, message: str) -> Dict[str, Any]:
        """
        调用 Agent 处理消息（模拟 LLM 调用）
        
        未来：实际调用 LLM API，注入 system prompt + tools
        """
        agent_info = self._registry.get(agent_name)
        if not agent_info:
            return {"error": f"Agent @{agent_name} 未注册"}
        
        # 生成 system prompt
        system_prompt = self.get_system_prompt(agent_name)
        tool_defs = self.get_tool_definitions(agent_name)
        
        return {
            "agent": agent_name,
            "response": f"[{agent_name}] 收到: {message}",
            "skills": [s.name for s in agent_info.skills],
            "tools_available": list(self._tool_functions.get(agent_name, {}).keys()),
            "system_prompt": system_prompt,
            "tool_definitions": tool_defs
        }
    
    # ─── Agent 管理器调用 ───
    
    def call_agent_manager(self, agent: AgentDef, test_report: str = "") -> Dict[str, Any]:
        """
        调用 Agent 管理器来修复或改进 Agent
        
        Args:
            agent: 需要修复的 Agent 定义
            test_report: 测试报告（用于指导修复）
        
        Returns:
            修复后的 Agent 定义或错误信息
        """
        from system.creator.creator import AgentCreator
        
        try:
            creator = AgentCreator()
            
            # 分析测试报告，提取需要修复的问题
            issues = self._analyze_test_report(test_report)
            
            if not issues:
                return {
                    "success": True,
                    "message": "Agent 测试通过，无需修复",
                    "agent": agent
                }
            
            # 根据问题生成修复建议
            fix_suggestions = self._generate_fix_suggestions(agent, issues)
            
            # 应用修复
            fixed_agent = self._apply_fixes(agent, fix_suggestions)
            
            # 重新测试
            result = creator.test_agent(fixed_agent)
            
            return {
                "success": result.passed,
                "message": "Agent 修复完成" if result.passed else "修复后测试仍未通过",
                "agent": fixed_agent,
                "issues": issues,
                "fixes_applied": fix_suggestions,
                "test_result": {
                    "passed": result.passed,
                    "errors": result.errors,
                    "duration_ms": result.duration_ms
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"调用 Agent 管理器失败: {str(e)}",
                "error": traceback.format_exc()
            }
    
    def _analyze_test_report(self, report: str) -> List[Dict[str, Any]]:
        """分析测试报告，提取问题"""
        issues = []
        
        if not report:
            return issues
        
        # 解析 Tool 测试失败
        tool_fail_pattern = r"### ❌ (\w+)"
        tool_matches = re.findall(tool_fail_pattern, report)
        for tool_name in tool_matches:
            issues.append({
                "type": "tool_failure",
                "tool_name": tool_name,
                "description": f"工具 {tool_name} 测试失败"
            })
        
        # 解析错误信息
        error_pattern = r"\*\*错误信息\*\*:\s*\n\s*- (.*)"
        error_matches = re.findall(error_pattern, report)
        for error in error_matches:
            issues.append({
                "type": "execution_error",
                "description": error.strip()
            })
        
        # 解析建议
        suggestion_pattern = r"\*\*建议\*\*:\s*\n\s*- (.*)"
        suggestion_matches = re.findall(suggestion_pattern, report)
        for suggestion in suggestion_matches:
            issues.append({
                "type": "recommendation",
                "description": suggestion.strip()
            })
        
        return issues
    
    def _generate_fix_suggestions(self, agent: AgentDef, issues: List[Dict]) -> List[Dict]:
        """根据问题生成修复建议"""
        suggestions = []
        
        for issue in issues:
            if issue["type"] == "tool_failure":
                tool = next((t for t in agent.tools if t.name == issue.get("tool_name")), None)
                if tool:
                    suggestions.append({
                        "tool_name": tool.name,
                        "action": "fix_tool",
                        "reason": issue["description"],
                        "suggestion": f"需要修复工具 {tool.name} 的代码"
                    })
            
            elif issue["type"] == "execution_error":
                if "NoneType" in issue["description"]:
                    suggestions.append({
                        "action": "add_default_params",
                        "reason": issue["description"],
                        "suggestion": "函数缺少默认参数，需要添加"
                    })
                else:
                    suggestions.append({
                        "action": "debug_code",
                        "reason": issue["description"],
                        "suggestion": "需要调试代码逻辑"
                    })
            
            elif issue["type"] == "recommendation":
                suggestions.append({
                    "action": "improve_documentation",
                    "reason": issue["description"],
                    "suggestion": issue["description"]
                })
        
        return suggestions
    
    def _apply_fixes(self, agent: AgentDef, fixes: List[Dict]) -> AgentDef:
        """应用修复到 Agent"""
        for fix in fixes:
            if fix["action"] == "add_default_params":
                for tool in agent.tools:
                    # 为没有默认参数的函数添加默认值
                    if tool.code and tool.name in fix.get("tool_name", ""):
                        tool.code = self._add_default_parameters(tool.code)
            
            elif fix["action"] == "fix_tool":
                tool_name = fix.get("tool_name")
                for tool in agent.tools:
                    if tool.name == tool_name:
                        # 简单修复：添加基本的错误处理
                        if not "try:" in tool.code:
                            tool.code = self._add_error_handling(tool.code)
        
        return agent
    
    def _add_default_parameters(self, code: str) -> str:
        """为函数添加默认参数"""
        try:
            # 简单的代码转换：在参数后添加 = None
            lines = code.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("def "):
                    # 找到函数定义行
                    func_def = line
                    # 在参数列表中添加默认值
                    if "(" in func_def and ")" in func_def:
                        params_part = func_def[func_def.index("(")+1:func_def.index(")")]
                        params = [p.strip() for p in params_part.split(",") if p.strip()]
                        params_with_default = [f"{p} = None" if "=" not in p else p for p in params]
                        new_params = ", ".join(params_with_default)
                        lines[i] = func_def.replace(params_part, new_params)
            return "\n".join(lines)
        except:
            return code
    
    def _add_error_handling(self, code: str) -> str:
        """添加错误处理（暂未实现——保留以供未来扩展）"""
        return code
    
    @staticmethod
    def _infer_type(annotation) -> str:
        if annotation is inspect.Parameter.empty:
            return "string"
        if annotation is str:
            return "string"
        if annotation is int:
            return "integer"
        if annotation is float:
            return "number"
        if annotation is bool:
            return "boolean"
        if annotation is list or annotation is List:
            return "array"
        if annotation is dict or annotation is Dict:
            return "object"
        return "string"
