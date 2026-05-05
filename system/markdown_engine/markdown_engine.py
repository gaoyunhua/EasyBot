#!/usr/bin/env python3
"""
EasyBot Markdown Engine - Unified Command Execution System for Agent Workflows
=====================================================

This engine provides a standardized way to define, parse, and execute agent commands
from markdown files. It supports multiple command types, priority handling, and
execution workflows.

Version: 2.0.0
Author: EasyBot System
"""

import sys
import re
import hashlib
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import base64

# Try to import additional dependencies
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


class CommandType(Enum):
    """Types of commands supported by the MarkdownEngine."""
    ACTION = "action"
    TASK = "task"
    CODE = "code"
    INFO = "info"
    STEP = "step"
    RULE = "rule"
    PARAM = "param"
    META = "meta"
    WORKFLOW = "workflow"


@dataclass
class CommandDefinition:
    """Represents a parsed command from markdown."""
    type: CommandType
    name: str
    content: str
    priority: int = 1
    description: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_file: str = ""
    source_line: int = 0
    tags: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class CommandContext:
    """Context for command execution."""
    agent_name: str
    workspace: Path
    timestamp: datetime = field(default_factory=datetime.now)
    variables: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)


class MarkdownEngine:
    """
    Core engine for reading, parsing, and executing commands from agent markdown files.
    
    This is the central component of the EasyBot system's agent workflow management.
    """
    
    def __init__(self, workspace_dir: Path = None):
        """Initialize the MarkdownEngine.
        
        Args:
            workspace_dir: Path to the workspace directory. If None, defaults to
                          the parent of this module.
        """
        self.workspace_dir = workspace_dir or Path(__file__).parent.parent.parent / "workspace"
        self.agent_dir = self.workspace_dir / "agent"
        self.command_registry: Dict[str, List[CommandDefinition]] = {}
        self._global_command_id = 0
        
    def get_agent_path(self, agent_name: str) -> Optional[Path]:
        """Get the path to an agent's markdown file."""
        agent_path = self.agent_dir / agent_name
        if agent_path.exists():
            md_path = agent_path / "agent.md"
            if md_path.exists():
                return md_path
        # Check for alternative file names
        for alt_name in ["agent.md", "instructions.md", "commands.md"]:
            alt_path = agent_path / alt_name
            if alt_path.exists():
                return alt_path
        return None
    
    def list_agents(self) -> List[str]:
        """List all agent directories."""
        agents = []
        if self.agent_dir.exists():
            for item in self.agent_dir.iterdir():
                if item.is_dir():
                    agents.append(item.name)
        return sorted(agents)
    
    def register_command(self, agent_name: str, command_type: CommandType, 
                        name: str, **kwargs) -> CommandDefinition:
        """Register a command to the registry.
        
        Args:
            agent_name: Name of the agent
            command_type: Type of command
            name: Command name
            **kwargs: Additional metadata
            
        Returns:
            CommandDefinition instance
        """
        cmd = CommandDefinition(
            type=command_type,
            name=name,
            content="",
            priority=kwargs.get("priority", 1),
            description=kwargs.get("description", ""),
            parameters=kwargs.get("parameters", {}),
            metadata=kwargs.get("metadata", {}),
            source_file="",
            source_line=0,
            enabled=kwargs.get("enabled", True)
        )
        self.command_registry.setdefault(agent_name, []).append(cmd)
        return cmd
    
    def read_markdown(self, agent_name: str, raw: bool = False) -> Dict[str, Any]:
        """Read and parse an agent's markdown file.
        
        Args:
            agent_name: Name of the agent
            raw: If True, return raw content without parsing
            
        Returns:
            Dictionary with parsed content
        """
        agent_path = self.get_agent_path(agent_name)
        
        if not agent_path:
            return {
                "agent_name": agent_name,
                "success": False,
                "error": f"Agent '{agent_name}' not found",
                "instructions": [],
                "raw_content": None
            }
        
        try:
            with open(agent_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {
                "agent_name": agent_name,
                "success": False,
                "error": f"Could not read agent.md: {e}",
                "instructions": [],
                "raw_content": None
            }
        
        result = {
            "agent_name": agent_name,
            "success": True,
            "raw_content": content,
            "instructions": self._parse_markdown(content)
        }
        
        if raw:
            result["raw_content"] = content
            
        return result
    
    def _parse_markdown(self, markdown: str) -> List[CommandDefinition]:
        """Parse markdown content into command definitions.
        
        Supports multiple markdown formats:
        - Standard list items (- or *)
        - YAML front matter
        - JSON code blocks
        - Custom command blocks
        
        Args:
            markdown: Raw markdown content
            
        Returns:
            List of CommandDefinition objects
        """
        # Get agent path for source file tracking
        agent_path = self.agent_dir / "test_agent"  # Default placeholder
        
        instructions = []
        lines = markdown.split('\n')
        current_section = None
        current_items = []
        in_code_block = False
        code_content = []
        in_yaml = False
        yaml_content = []
        command_line = 0
        
        for line_num, line in enumerate(lines, 1):
            # Handle YAML front matter
            if line.strip().startswith("---"):
                if not in_yaml:
                    in_yaml = True
                    yaml_content = []
                    continue
                else:
                    in_yaml = False
                    if yaml_content:
                        try:
                            yaml_data = yaml.safe_load('\n'.join(yaml_content))
                            result["metadata"] = yaml_data or {}
                        except:
                            pass
                    continue
            
            # Handle code blocks
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    current_section = None
                    code_content = []
                    continue
                else:
                    in_code_block = False
                    code_block = '\n'.join(code_content).strip()
                    if code_block:
                        # Try to parse as JSON
                        if code_block.startswith('{'):
                            try:
                                meta = json.loads(code_block)
                                for instr in current_items:
                                    instr.metadata.update(meta)
                            except:
                                pass
                        if code_block:
                            instructions.append(CommandDefinition(
                                type=CommandType.CODE,
                                name=code_block[:50] if len(code_block) < 50 else "..." + code_block[-47:],
                                content=code_block,
                                priority=0
                            ))
                    code_content = []
                continue
            
            # Skip code block lines
            if in_code_block:
                code_content.append(line)
                continue
            
            # Check for section headers
            section_match = re.match(r'^#{1,6}\s+(.+)$', line.strip())
            if section_match:
                if current_section:
                    # Process previous section items
                    if current_items and current_section in ["actions", "instructions", "commands"]:
                        for item in current_items:
                            instructions.append(CommandDefinition(
                                type=item.type,
                                name=item.name,
                                content=item.content,
                                priority=item.priority,
                                description=item.description,
                                parameters=item.parameters,
                                metadata=item.metadata,
                                source_file=str(agent_path),
                                source_line=command_line,
                                tags=item.tags,
                                enabled=item.enabled
                            ))
                current_section = section_match.group(1).lower().strip()
                command_line = line_num
                current_items = []
                continue
            
            # Check for custom command blocks
            cmd_block_match = re.match(r'^##\s*Command\s*:?\s*`?([\w-]+)`?\s*:\s*(.*)$', line.strip())
            if cmd_block_match and current_section == "commands":
                cmd_name = cmd_block_match.group(1).strip()
                cmd_desc = cmd_block_match.group(2).strip()
                if current_items:
                    for item in current_items:
                        instructions.append(CommandDefinition(
                            type=CommandType.ACTION,
                            name=item.name,
                            content=item.content,
                            priority=item.priority,
                            description=item.description,
                            parameters=item.parameters,
                            metadata=item.metadata,
                            source_file=str(agent_path),
                            source_line=command_line,
                            tags=item.tags,
                            enabled=item.enabled
                        ))
                instructions.append(CommandDefinition(
                    type=CommandType.ACTION,
                    name=cmd_name,
                    content=cmd_desc,
                    priority=5
                ))
                current_section = "commands"
                continue
            
            # Check for task section (## Task:)
            task_match = re.match(r'^##\s*Task\s*:?\s*(.+)$', line.strip(), re.IGNORECASE)
            if task_match:
                if current_section:
                    if current_items:
                        for item in current_items:
                            instructions.append(CommandDefinition(
                                type=item.type,
                                name=item.name,
                                content=item.content,
                                priority=item.priority,
                                description=item.description,
                                parameters=item.parameters,
                                metadata=item.metadata,
                                source_file=str(agent_path),
                                source_line=command_line,
                                tags=item.tags,
                                enabled=item.enabled
                            ))
                instructions.append(CommandDefinition(
                    type=CommandType.TASK,
                    name=task_match.group(1).strip(),
                    content=line.strip(),
                    priority=10
                ))
                current_section = "tasks"
                continue
            
            # Check for action lists
            action_match = re.match(r'^[-*]\s*(.+)$', line.strip())
            if action_match and current_section in ["actions", "instructions", "commands"]:
                current_items.append(CommandDefinition(
                    type=CommandType.ACTION,
                    name=line.strip(),
                    content=line.strip(),
                    priority=5,
                    description="",
                    parameters={},
                    metadata={},
                    tags=[],
                    enabled=True
                ))
                continue
            
            # Check for info sections
            info_match = re.match(r'^##\s*Info\s*:?\s*(.+)$', line.strip(), re.IGNORECASE)
            if info_match:
                if current_section:
                    if current_items:
                        for item in current_items:
                            instructions.append(CommandDefinition(
                                type=item.type,
                                name=item.name,
                                content=item.content,
                                priority=item.priority,
                                description=item.description,
                                parameters=item.parameters,
                                metadata=item.metadata,
                                source_file=str(agent_path),
                                source_line=command_line,
                                tags=item.tags,
                                enabled=item.enabled
                            ))
                instructions.append(CommandDefinition(
                    type=CommandType.INFO,
                    name=info_match.group(1).strip(),
                    content=line.strip(),
                    priority=20
                ))
                current_section = "info"
                continue
            
            # Check for param definitions
            param_match = re.match(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*[:=]\s*(.+)$', line.strip())
            if param_match and current_section in ["actions", "instructions", "commands"]:
                current_items[-1].parameters[param_match.group(1).strip()] = param_match.group(2).strip()
                continue
            
            # Check for tags
            tag_match = re.match(r'^##\s*Tags\s*:\s*(.+)$', line.strip(), re.IGNORECASE)
            if tag_match:
                current_items[-1].tags = tag_match.group(1).split()
                continue
            
            # Check for enable/disable
            if line.strip() in ["--", "## Disabled", "## enabled"]:
                current_items[-1].enabled = line.strip() != "--"
                continue
        
        # Process remaining items
        if current_section and current_items:
            for item in current_items:
                instructions.append(CommandDefinition(
                    type=item.type,
                    name=item.name,
                    content=item.content,
                    priority=item.priority,
                    description=item.description,
                    parameters=item.parameters,
                    metadata=item.metadata,
                    source_file=str(agent_path),
                    source_line=command_line,
                    tags=item.tags,
                    enabled=item.enabled
                ))
        
        return instructions
    
    def list_actions(self, agent_name: str, enabled_only: bool = True) -> List[str]:
        """List all actions from an agent's markdown.
        
        Args:
            agent_name: Name of the agent
            enabled_only: If True, only return enabled commands
            
        Returns:
            List of action strings
        """
        result = self.read_markdown(agent_name)
        if not result["success"]:
            return []
        
        actions = []
        for instr in result["instructions"]:
            if instr.type == CommandType.ACTION:
                if not enabled_only or instr.enabled:
                    actions.append(instr.content)
        
        return actions
    
    def list_tasks(self, agent_name: str, enabled_only: bool = True) -> List[str]:
        """List all tasks from an agent's markdown.
        
        Args:
            agent_name: Name of the agent
            enabled_only: If True, only return enabled commands
            
        Returns:
            List of task strings
        """
        result = self.read_markdown(agent_name)
        if not result["success"]:
            return []
        
        tasks = []
        for instr in result["instructions"]:
            if instr.type == CommandType.TASK:
                if not enabled_only or instr.enabled:
                    tasks.append(instr.content)
        
        return tasks
    
    def list_code_blocks(self, agent_name: str) -> List[str]:
        """List all code blocks from an agent's markdown.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of code block contents
        """
        result = self.read_markdown(agent_name)
        if not result["success"]:
            return []
        
        code_blocks = []
        for instr in result["instructions"]:
            if instr.type == CommandType.CODE:
                code_blocks.append(instr.content)
        
        return code_blocks
    
    def get_full_markdown(self, agent_name: str) -> Optional[str]:
        """Get the full raw markdown content.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Raw markdown content or None
        """
        result = self.read_markdown(agent_name)
        if not result["success"]:
            return None
        
        # agent_path is not in the result dict, use the agent directory
        agent_path = self.agent_dir / agent_name
        return result.get("raw_content") if result["success"] else None
    
    def get_command_count(self, agent_name: str) -> int:
        """Get the total number of commands for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Total command count
        """
        result = self.read_markdown(agent_name)
        if not result["success"]:
            return 0
        
        return len(result["instructions"])
    
    def get_command_breakdown(self, agent_name: str) -> Dict[str, int]:
        """Get a breakdown of command types for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with command type counts
        """
        result = self.read_markdown(agent_name)
        if not result["success"]:
            return {}
        
        breakdown = {}
        for instr in result["instructions"]:
            breakdown[instr.type.value] = breakdown.get(instr.type.value, 0) + 1
        
        return breakdown
    
    def execute_command(self, agent_name: str, command: str, 
                       context: CommandContext = None) -> Dict[str, Any]:
        """Execute a specific command from the agent's markdown.
        
        Args:
            agent_name: Name of the agent
            command: Command name to execute
            context: Optional context for execution
            
        Returns:
            Execution result
        """
        context = context or CommandContext(agent_name=agent_name, workspace=self.workspace_dir)
        
        result = self.read_markdown(agent_name)
        if not result["success"]:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found",
                "command": command
            }
        
        for instr in result["instructions"]:
            if instr.type == CommandType.ACTION and instr.name == command:
                if not instr.enabled:
                    return {
                        "success": False,
                        "error": f"Command '{command}' is disabled",
                        "command": command
                    }
                
                context.variables[instr.name] = instr.content
                context.history.append({
                    "command": command,
                    "timestamp": context.timestamp.isoformat(),
                    "content": instr.content,
                    "type": instr.type.value
                })
                
                # Execute the command
                result = self._execute_command_content(instr.content, context)
                
                return {
                    "success": True,
                    "command": command,
                    "content": instr.content,
                    "context": context,
                    "result": result
                }
        
        return {
            "success": False,
            "error": f"Command '{command}' not found in {agent_name}",
            "command": command
        }
    
    def _execute_command_content(self, content: str, context: CommandContext) -> Dict[str, Any]:
        """Execute a command's content.
        
        Args:
            content: Command content to execute
            context: Execution context
            
        Returns:
            Execution result
        """
        try:
            # Try to execute as Python code
            if content.startswith('```python') or content.startswith('```'):
                code = content.split('```', 1)[1] if '```' in content else ""
                if context.variables:
                    code = code.format(**context.variables)
                exec_globals = {"__builtins__": __builtins__, **context.variables}
                exec(code, exec_globals)
                return {"result": "executed", "output": exec_globals}
            else:
                return {"result": f"Command executed: {content}"}
        except Exception as e:
            return {"error": str(e)}
    
    def execute_all_actions(self, agent_name: str, 
                           context: CommandContext = None) -> Dict[str, Any]:
        """Execute all actions from an agent's markdown.
        
        Args:
            agent_name: Name of the agent
            context: Optional context for execution
            
        Returns:
            Execution result
        """
        context = context or CommandContext(agent_name=agent_name, workspace=self.workspace_dir)
        actions = self.list_actions(agent_name)
        
        if not actions:
            return {
                "success": True,
                "message": f"No actions found for {agent_name}",
                "agent": agent_name
            }
        
        results = []
        all_success = True
        for action in actions:
            result = self.execute_command(agent_name, action, context)
            results.append(result)
            if not result.get("success"):
                all_success = False
        
        return {
            "success": all_success,
            "agent": agent_name,
            "actions_executed": len(actions),
            "results": results
        }
    
    def search_commands(self, agent_name: str, query: str, 
                       type_filter: List[CommandType] = None) -> List[Dict[str, Any]]:
        """Search for commands matching a query.
        
        Args:
            agent_name: Name of the agent
            query: Search query string
            type_filter: Optional filter for command types
            
        Returns:
            List of matching commands with metadata
        """
        result = self.read_markdown(agent_name)
        if not result["success"]:
            return []
        
        agent_path = self.agent_dir / agent_name  # Use agent path for source file tracking
        queries = query.lower().split()
        matches = []
        
        for instr in result["instructions"]:
            if not instr.enabled:
                continue
            
            # Check if query matches content, name, or description
            match = any(term in instr.name.lower() or term in instr.content.lower() 
                      or term in instr.description.lower() for term in queries)
            
            if match:
                match_info = {
                    "command": instr.content,
                    "name": instr.name,
                    "type": instr.type.value,
                    "source": str(agent_path),
                    "line": instr.source_line,
                    "enabled": instr.enabled
                }
                if type_filter:
                    match_info["type_filter"] = instr.type in type_filter
                
                matches.append(match_info)
        
        return matches
    
    def generate_agent_manifest(self, agent_name: str) -> Dict[str, Any]:
        """Generate a manifest of the agent's capabilities.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent manifest with all capabilities
        """
        result = self.read_markdown(agent_name)
        if not result["success"]:
            return {"agent": agent_name, "success": False}
        
        # Use agent directory for file path
        agent_path = self.agent_dir / agent_name
        
        manifest = {
            "agent_name": agent_name,
            "file": str(agent_path),
            "created_at": datetime.now().isoformat(),
            "metadata": result.get("metadata", {}),
            "commands": {
                "total": len(result["instructions"]),
                "by_type": self.get_command_breakdown(agent_name),
                "by_name": {}
            },
            "capabilities": []
        }
        
        for instr in result["instructions"]:
            manifest["commands"]["by_name"][instr.name] = {
                "type": instr.type.value,
                "enabled": instr.enabled
            }
            manifest["capabilities"].append({
                "name": instr.name,
                "type": instr.type.value,
                "description": instr.description,
                "priority": instr.priority
            })
        
        return manifest


class MarkdownCommandExecutor:
    """Command-line executor for markdown instructions."""
    
    def __init__(self, workspace_dir: Path = None):
        """Initialize with workspace directory."""
        self.workspace_dir = workspace_dir or Path(__file__).parent.parent.parent / "workspace"
        self.engine = MarkdownEngine(workspace_dir)
    
    def list_agents(self) -> List[str]:
        """List all agents."""
        return self.engine.list_agents()
    
    def display_markdown(self, agent_name: str) -> bool:
        """Display an agent's markdown content."""
        result = self.engine.read_markdown(agent_name)
        
        if not result["success"]:
            print(f"❌ Error: {result['error']}")
            return False
        
        print(f"\n{'=' * 60}")
        print(f"📄 {agent_name}/agent.md")
        print('=' * 60)
        print(result["raw_content"])
        print('=' * 60)
        
        return True
    
    def show_actions(self, agent_name: str) -> bool:
        """Show actions from an agent's markdown."""
        actions = self.engine.list_actions(agent_name)
        
        if not actions:
            print(f"No actions found for {agent_name}")
            return False
        
        print(f"\n📋 Actions ({len(actions)}):")
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {action}")
        
        return True
    
    def show_tasks(self, agent_name: str) -> bool:
        """Show tasks from an agent's markdown."""
        tasks = self.engine.list_tasks(agent_name)
        
        if not tasks:
            print(f"No tasks found for {agent_name}")
            return False
        
        print(f"\n📋 Tasks ({len(tasks)}):")
        for i, task in enumerate(tasks, 1):
            print(f"  {i}. {task}")
        
        return True
    
    def show_code_blocks(self, agent_name: str) -> bool:
        """Show code blocks from an agent's markdown."""
        code_blocks = self.engine.list_code_blocks(agent_name)
        
        if not code_blocks:
            print(f"No code blocks found for {agent_name}")
            return False
        
        print(f"\n📋 Code Blocks ({len(code_blocks)}):")
        for i, code in enumerate(code_blocks, 1):
            print(f"  {i}. ```\n{code}\n```")
        
        return True
    
    def show_search_results(self, agent_name: str, query: str) -> bool:
        """Show search results for a query."""
        results = self.engine.search_commands(agent_name, query)
        
        if not results:
            print(f"No matching commands found for '{query}'")
            return False
        
        print(f"\n🔍 Search results for '{query}' ({len(results)} matches):")
        for i, result in enumerate(results, 1):
            print(f"  {i}. [{result['type'].upper()}] {result['command']}")
            print(f"     Source: {result['source']}:{result['line']}")
        
        return True
    
    def run_all_markdowns(self):
        """Run markdown commands for all agents."""
        agents = self.list_agents()
        
        if not agents:
            print("No agents found.")
            return
        
        print(f"Processing {len(agents)} agents...\n")
        
        for agent_name in agents:
            print(f"\n{'=' * 60}")
            print(f"🔍 {agent_name}")
            print('=' * 60)
            
            # Show actions
            self.show_actions(agent_name)
            
            # Show tasks
            self.show_tasks(agent_name)
            
            # Show code blocks
            self.show_code_blocks(agent_name)
        
        print(f"\n{'=' * 60}")
        print(f"✅ Completed processing {len(agents)} agents")
        print('=' * 60)


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Markdown Engine - Command execution for agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m system.markdown_engine --agent greeting_agent
  python -m system.markdown_engine --actions greeting_agent
  python -m system.markdown_engine --search "python" calculator
        """
    )
    
    parser.add_argument(
        "--agent", 
        type=str,
        required=True,
        help="Agent name to process"
    )
    parser.add_argument(
        "--actions",
        action="store_true",
        help="Show actions from markdown"
    )
    parser.add_argument(
        "--tasks",
        action="store_true",
        help="Show tasks from markdown"
    )
    parser.add_argument(
        "--code-blocks",
        action="store_true",
        help="Show code blocks from markdown"
    )
    parser.add_argument(
        "--search",
        type=str,
        default="",
        help="Search for commands"
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Display full markdown content"
    )
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="Generate agent manifest"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute all actions from markdown"
    )
    
    args = parser.parse_args()
    
    executor = MarkdownCommandExecutor()
    
    if args.search:
        executor.show_search_results(args.agent, args.search)
    elif args.actions:
        executor.show_actions(args.agent)
    elif args.tasks:
        executor.show_tasks(args.agent)
    elif args.code_blocks:
        executor.show_code_blocks(args.agent)
    elif args.display:
        executor.display_markdown(args.agent)
    elif args.manifest:
        manifest = executor.engine.generate_agent_manifest(args.agent)
        print(json.dumps(manifest, indent=2))
    elif args.execute:
        executor.run_all_markdowns()
    else:
        print(f"Error: Please specify --actions, --tasks, --code-blocks, --search, --display, or --execute")
        parser.print_help()


if __name__ == "__main__":
    main()
