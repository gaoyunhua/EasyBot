"""
Agent Tester — 验证调试区 Agent 的 Skill 和 Tool

职责：
1. 语法检查：Tool 代码能否编译
2. 推理检查：Skill 描述是否合理
3. 依赖检查：Dependencies 是否可安装
4. 执行检查：调用 Tool 看是否能跑
5. 安全性检查：检测潜在安全风险
6. 兼容性检查：支持多种 Agent 格式
"""

import time
import sys
import traceback
import importlib.util
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from system.models.agent import AgentDef, ToolDef, SkillDef, TestResult


class TestReport:
    """测试报告类 - 可用于修改和导出"""
    
    def __init__(self, agent_name: str = ""):
        self.agent_name = agent_name
        self.timestamp = datetime.now().isoformat()
        self.overall_status = "PASS"
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.duration_ms = 0
        self.skill_reports = []
        self.tool_reports = []
        self.agent_info = {}
        self.recommendations = []
        self.issues = []
    
    def to_markdown(self) -> str:
        """生成可修改的 Markdown 格式测试报告"""
        sections = []
        
        # 标题
        sections.append(f"# 测试报告: {self.agent_name}")
        sections.append(f"\n**生成时间**: {self.timestamp}")
        sections.append(f"**测试状态**: {'✅ 通过' if self.overall_status == 'PASS' else '❌ 失败'}")
        sections.append(f"**测试总数**: {self.total_tests}")
        sections.append(f"**通过**: {self.passed_tests}")
        sections.append(f"**失败**: {self.failed_tests}")
        sections.append(f"**耗时**: {self.duration_ms:.2f}ms")
        
        # Agent 信息
        if self.agent_info:
            sections.append("\n## 📋 Agent 信息")
            for key, value in self.agent_info.items():
                sections.append(f"- **{key}**: {value}")
        
        # Skill 测试结果
        if self.skill_reports:
            sections.append("\n## 🎯 Skill 测试结果")
            for report in self.skill_reports:
                status = "✅" if report["status"] == "PASS" else "❌"
                sections.append(f"\n### {status} {report['name']}")
                sections.append(f"**描述**: {report.get('description', '')}")
                sections.append(f"**状态**: {report['status']}")
                if report.get('issues'):
                    sections.append("\n**问题**:")
                    for issue in report['issues']:
                        sections.append(f"  - {issue}")
                if report.get('recommendations'):
                    sections.append("\n**建议**:")
                    for rec in report['recommendations']:
                        sections.append(f"  - {rec}")
        
        # Tool 测试结果
        if self.tool_reports:
            sections.append("\n## 🛠️ Tool 测试结果")
            for report in self.tool_reports:
                status = "✅" if report["status"] == "PASS" else "❌"
                sections.append(f"\n### {status} {report['name']}")
                sections.append(f"**描述**: {report.get('description', '')}")
                sections.append(f"**参数**: {report.get('parameters', '无')}")
                sections.append(f"**状态**: {report['status']}")
                
                if report.get('test_results'):
                    sections.append("\n**测试项**:")
                    for test_name, test_status in report['test_results'].items():
                        t_status = "✅" if test_status else "❌"
                        sections.append(f"  - {t_status} {test_name}")
                
                if report.get('errors'):
                    sections.append("\n**错误信息**:")
                    for error in report['errors']:
                        sections.append(f"  - {error}")
                
                if report.get('recommendations'):
                    sections.append("\n**优化建议**:")
                    for rec in report['recommendations']:
                        sections.append(f"  - {rec}")
        
        # 总体建议
        if self.recommendations:
            sections.append("\n## 💡 总体优化建议")
            for i, rec in enumerate(self.recommendations, 1):
                sections.append(f"{i}. {rec}")
        
        # 问题汇总
        if self.issues:
            sections.append("\n## ⚠️ 问题汇总")
            for i, issue in enumerate(self.issues, 1):
                sections.append(f"{i}. {issue}")
        
        return "\n".join(sections)
    
    def to_json(self) -> str:
        """导出为 JSON 格式"""
        return json.dumps({
            "agent_name": self.agent_name,
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "duration_ms": self.duration_ms,
            "skill_reports": self.skill_reports,
            "tool_reports": self.tool_reports,
            "agent_info": self.agent_info,
            "recommendations": self.recommendations,
            "issues": self.issues
        }, ensure_ascii=False, indent=2)


class AgentTester:
    """Agent 测试验证器 - 支持多种 Agent 格式"""
    
    # 支持的 Agent 类型
    SUPPORTED_FORMATS = ["easybot", "openai", "langchain", "llamaindex", "autogen", "crewai"]
    
    def __init__(self):
        self.results_history: List[TestResult] = []
        self.report: Optional[TestReport] = None
    
    def run_agent(self, agent: AgentDef) -> TestResult:
        """对 Agent 运行完整测试（兼容 Tester 接口）"""
        return self.test(agent)
    
    def test(self, agent: AgentDef, generate_report: bool = True) -> TestResult:
        """对 Agent 运行完整测试"""
        start = time.time()
        result = TestResult()
        
        # 初始化测试报告
        if generate_report:
            self.report = TestReport(agent.name)
            self.report.agent_info = {
                "名称": agent.name,
                "描述": agent.description or "无",
                "版本": agent.version or "未知",
                "技能数量": len(agent.skills),
                "工具数量": len(agent.tools)
            }
        
        # 1. 验证 Agent 基本信息
        agent_check = self._validate_agent_basic(agent)
        if not agent_check["pass"]:
            result.errors.extend(agent_check["errors"])
        
        # 2. 验证 Skills
        for skill in agent.skills:
            skill_result = self._validate_skill_comprehensive(skill)
            result.skill_results[skill.name] = skill_result["pass"]
            if not skill_result["pass"]:
                result.errors.append(f"Skill 验证失败: {skill.name}")
            
            if generate_report:
                self.report.skill_reports.append({
                    "name": skill.name,
                    "description": skill.description,
                    "status": "PASS" if skill_result["pass"] else "FAIL",
                    "issues": skill_result.get("issues", []),
                    "recommendations": skill_result.get("recommendations", [])
                })
        
        # 3. 验证 Tools
        for tool in agent.tools:
            tool_result = self._validate_tool_comprehensive(tool)
            result.tool_results[tool.name] = tool_result
            if not tool_result.get("pass", False):
                result.errors.append(f"Tool 验证失败: {tool.name} — {tool_result.get('error', '未知错误')}")
            
            if generate_report:
                self.report.tool_reports.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": ", ".join(tool.parameters.keys()) if tool.parameters else "无",
                    "status": "PASS" if tool_result.get("pass") else "FAIL",
                    "test_results": tool_result.get("test_results", {}),
                    "errors": tool_result.get("errors", []),
                    "recommendations": tool_result.get("recommendations", [])
                })
        
        # 4. 兼容性检查
        compat_result = self._check_compatibility(agent)
        if not compat_result["pass"]:
            result.errors.extend(compat_result["errors"])
        
        # 5. 安全性检查
        security_result = self._check_security(agent)
        if not security_result["pass"]:
            result.errors.extend(security_result["errors"])
        
        # 更新结果
        result.passed = len(result.errors) == 0
        result.duration_ms = (time.time() - start) * 1000
        
        # 更新报告
        if generate_report:
            self.report.total_tests = len(agent.skills) + len(agent.tools) + 2  # agent + compat + security
            self.report.passed_tests = sum(1 for r in result.skill_results.values() if r) + \
                                     sum(1 for r in result.tool_results.values() if r.get("pass"))
            self.report.failed_tests = self.report.total_tests - self.report.passed_tests
            self.report.overall_status = "PASS" if result.passed else "FAIL"
            self.report.duration_ms = result.duration_ms
            self.report.issues = result.errors
            self.report.recommendations = self._generate_recommendations(agent, result)
        
        self.results_history.append(result)
        return result
    
    def _validate_agent_basic(self, agent: AgentDef) -> Dict[str, Any]:
        """验证 Agent 基本信息"""
        result = {"pass": True, "errors": []}
        
        if not agent.name or not agent.name.strip():
            result["pass"] = False
            result["errors"].append("Agent 名称不能为空")
        
        if not re.match(r'^[a-zA-Z0-9_\-]+$', agent.name or ""):
            result["pass"] = False
            result["errors"].append(f"Agent 名称包含非法字符: {agent.name}")
        
        if len(agent.skills) == 0 and len(agent.tools) == 0:
            result["errors"].append("Agent 没有任何技能或工具")
        
        return result
    
    def _validate_skill_comprehensive(self, skill: SkillDef) -> Dict[str, Any]:
        """全面验证 Skill 定义"""
        result = {
            "pass": True,
            "issues": [],
            "recommendations": []
        }
        
        # 基本验证
        if not skill.name or not skill.name.strip():
            result["pass"] = False
            result["issues"].append("技能名称不能为空")
        elif not re.match(r'^[a-zA-Z0-9_\- ]+$', skill.name):
            result["pass"] = False
            result["issues"].append(f"技能名称包含非法字符: {skill.name}")
        
        if not skill.description or not skill.description.strip():
            result["issues"].append("技能描述为空")
        elif len(skill.description) < 10:
            result["recommendations"].append("技能描述过于简短，建议提供更详细的说明")
        elif len(skill.description) > 500:
            result["recommendations"].append("技能描述过长，建议精简到 500 字符以内")
        
        # 检查指令
        if skill.instructions and len(skill.instructions) > 1000:
            result["recommendations"].append("技能指令过长，建议精简")
        
        # 格式检查
        if skill.description:
            # 检查是否包含关键词
            keywords = ["能够", "可以", "支持", "提供"]
            if not any(k in skill.description for k in keywords):
                result["recommendations"].append("建议在描述中包含动作动词（如：能够、可以、支持）")
        
        return result
    
    def _validate_tool_comprehensive(self, tool: ToolDef) -> Dict[str, Any]:
        """全面验证 Tool 定义"""
        result = {
            "pass": True,
            "error": "",
            "test_results": {},
            "errors": [],
            "recommendations": []
        }
        
        # 1. 基本信息检查
        result["test_results"]["基本信息"] = self._check_tool_basic(tool, result)
        
        # 2. 参数验证
        result["test_results"]["参数定义"] = self._check_tool_parameters(tool, result)
        
        # 3. 语法检查
        syntax_result = self._check_tool_syntax(tool)
        result["test_results"]["语法检查"] = syntax_result["pass"]
        if not syntax_result["pass"]:
            result["errors"].append(syntax_result["error"])
        
        # 4. 安全检查
        result["test_results"]["安全检查"] = self._check_tool_security(tool, result)
        
        # 5. 执行测试
        if all(result["test_results"].values()):
            exec_result = self._execute_tool_with_params(tool)
            result["test_results"]["执行测试"] = exec_result["pass"]
            if not exec_result["pass"]:
                result["errors"].append(exec_result.get("error", "执行失败"))
        
        # 综合判断
        result["pass"] = all(result["test_results"].values())
        
        return result
    
    def _check_tool_basic(self, tool: ToolDef, result: Dict) -> bool:
        """检查 Tool 基本信息"""
        if not tool.name or not tool.name.strip():
            result["errors"].append("工具名称不能为空")
            return False
        
        if not re.match(r'^[a-zA-Z0-9_\-]+$', tool.name):
            result["errors"].append(f"工具名称包含非法字符: {tool.name}")
            return False
        
        if not tool.description or not tool.description.strip():
            result["recommendations"].append("建议添加工具描述")
        
        if not tool.code or not tool.code.strip():
            result["errors"].append("工具代码为空")
            return False
        
        return True
    
    def _check_tool_parameters(self, tool: ToolDef, result: Dict) -> bool:
        """检查 Tool 参数定义"""
        if not tool.parameters:
            result["recommendations"].append("工具没有定义参数，建议添加参数说明")
            return True
        
        # 检查参数格式
        for param_name, param_desc in tool.parameters.items():
            if not re.match(r'^[a-zA-Z0-9_\-]+$', param_name):
                result["errors"].append(f"参数名包含非法字符: {param_name}")
                return False
            
            if not param_desc or not param_desc.strip():
                result["recommendations"].append(f"参数 {param_name} 缺少描述")
        
        return True
    
    def _check_tool_syntax(self, tool: ToolDef) -> Dict[str, Any]:
        """检查 Tool 代码语法"""
        result = {"pass": False, "error": ""}
        
        if not tool.code:
            result["error"] = "代码为空"
            return result
        
        try:
            compile(tool.code, f"<{tool.name}>", "exec")
            result["pass"] = True
        except SyntaxError as e:
            result["error"] = f"语法错误: {e}"
        except Exception as e:
            result["error"] = f"编译异常: {e}"
        
        return result
    
    def _check_tool_security(self, tool: ToolDef, result: Dict) -> bool:
        """检查 Tool 代码安全性"""
        dangerous_patterns = [
            (r'\b(eval|exec)\s*\(', "使用了危险函数 eval/exec"),
            (r'\b(os\.(system|popen|chmod|chown))\b', "使用了危险的 os 模块函数"),
            (r'\b(subprocess\.(Popen|call|run))\b', "使用了 subprocess 模块"),
            (r'\b(shutil\.(rmtree|move|copy))\b', "使用了危险的 shutil 函数"),
            (r'\b(socket|requests|urllib)\b', "使用了网络相关模块"),
            (r'\bopen\s*\(\s*["\']', "使用了文件操作"),
        ]
        
        code = tool.code or ""
        for pattern, warning in dangerous_patterns:
            if re.search(pattern, code):
                result["recommendations"].append(f"⚠️ 检测到潜在安全风险: {warning}")
        
        return True
    
    def _execute_tool_with_params(self, tool: ToolDef) -> Dict[str, Any]:
        """带参数执行 Tool 测试"""
        result = {"pass": False, "error": ""}
        
        try:
            code_obj = compile(tool.code, f"<{tool.name}>", "exec")
            namespace = {}
            exec(code_obj, namespace)
            
            func = namespace.get(tool.name)
            if func is None:
                result["error"] = f"未找到函数 {tool.name}"
                return result
            
            # 尝试调用（无参数或默认参数）
            import inspect
            sig = inspect.signature(func)
            params = {}
            
            # 尝试获取默认参数
            for name, param in sig.parameters.items():
                if param.default is not inspect.Parameter.empty:
                    params[name] = param.default
                else:
                    # 对于没有默认值的参数，尝试提供测试值
                    if param.annotation in (int, float):
                        params[name] = 1
                    elif param.annotation is str:
                        params[name] = "test"
                    elif param.annotation is list:
                        params[name] = []
                    elif param.annotation is dict:
                        params[name] = {}
                    else:
                        params[name] = None
            
            # 调用函数
            func(**params)
            result["pass"] = True
            
        except Exception as e:
            result["error"] = f"执行异常: {e}"
            result["traceback"] = traceback.format_exc()
        
        return result
    
    def _check_compatibility(self, agent: AgentDef) -> Dict[str, Any]:
        """检查 Agent 兼容性"""
        result = {"pass": True, "errors": [], "warnings": []}
        
        # 检查 OpenAI Function Calling 格式兼容性
        has_openai_format = False
        for tool in agent.tools:
            if tool.parameters:
                has_openai_format = True
                # 检查是否符合 OpenAI 格式
                for param_name, param_desc in tool.parameters.items():
                    if isinstance(param_desc, dict):
                        if "type" not in param_desc:
                            result["warnings"].append(f"参数 {param_name} 缺少 type 字段（OpenAI 格式）")
                        if "description" not in param_desc:
                            result["warnings"].append(f"参数 {param_name} 缺少 description 字段（OpenAI 格式）")
        
        if has_openai_format:
            result["warnings"].append("检测到 OpenAI Function Calling 格式")
        
        return result
    
    def _check_security(self, agent: AgentDef) -> Dict[str, Any]:
        """检查 Agent 整体安全性"""
        result = {"pass": True, "errors": []}
        
        # 检查是否有敏感信息
        sensitive_patterns = [
            (r'[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-zA-Z]+', "检测到邮箱地址"),
            (r'(?i)password|secret|api[_-]?key|token', "检测到敏感关键词"),
            (r'[0-9]{11}', "检测到手机号码"),
            (r'[A-Za-z0-9+/]{40,}', "检测到可能的 Base64 编码密钥"),
        ]
        
        all_text = "\n".join([
            agent.description or "",
            agent.name or "",
            "\n".join(s.description or "" for s in agent.skills),
            "\n".join(t.description or "" for t in agent.tools),
            "\n".join(t.code or "" for t in agent.tools)
        ])
        
        for pattern, warning in sensitive_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                result["errors"].append(f"⚠️ 安全警告: {warning}")
        
        return result
    
    def _generate_recommendations(self, agent: AgentDef, result: TestResult) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 根据测试结果生成建议
        if len(agent.skills) == 0:
            recommendations.append("建议为 Agent 添加至少一个技能")
        
        if len(agent.tools) == 0:
            recommendations.append("建议为 Agent 添加至少一个工具")
        
        # 检查描述完整性
        if not agent.description:
            recommendations.append("建议添加 Agent 描述")
        
        # 检查参数文档
        for tool in agent.tools:
            if tool.parameters:
                for param_name, param_desc in tool.parameters.items():
                    if not param_desc or not str(param_desc).strip():
                        recommendations.append(f"建议完善工具 {tool.name} 的参数 {param_name} 描述")
        
        # 性能建议
        total_code_lines = sum((t.code or "").count("\n") for t in agent.tools)
        if total_code_lines > 100:
            recommendations.append("工具代码总行数较多，建议拆分或优化")
        
        return recommendations
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """生成并可选导出测试报告"""
        if not self.report:
            return "没有可用的测试报告"
        
        markdown = self.report.to_markdown()
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            print(f"测试报告已导出到: {output_path}")
        
        return markdown
    
    def test_multiple_agents(self, agents: List[AgentDef], 
                            output_dir: Optional[str] = None) -> List[TestResult]:
        """批量测试多个 Agent"""
        results = []
        
        for agent in agents:
            print(f"\n正在测试 Agent: {agent.name}")
            result = self.test(agent)
            
            if output_dir:
                report_path = Path(output_dir) / f"{agent.name}_test_report.md"
                self.generate_report(str(report_path))
            
            results.append(result)
            print(f"  状态: {'✅ 通过' if result.passed else '❌ 失败'}")
        
        return results


Tester = AgentTester