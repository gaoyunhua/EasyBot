#!/usr/bin/env python3
"""EasyBot - Agent Builder System Main Module
=====================================================

A lightweight Python system for generating and managing simple agent folders.
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root directory to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from system.caller.caller import AgentCaller
from system.creator.creator import AgentCreator
from system.tester.tester import Tester
from system.messager.messager import Messager
from system.markdown_engine.markdown_engine import MarkdownEngine, CommandType
from system.markdown_engine.agent_conversation import AgentConversation, create_conversation
from system.markdown_engine.message_handler import (
    MessageHandler,
    MessageRouter,
    InteractiveMessageHandler,
)
from system import init_globals, WORKSPACE, MODEL_PROVIDER, CONNECTOR

def _get_workspace_dir() -> Path:
    """获取 workspace 目录（按需创建）"""
    ws_dir = ROOT_DIR / "workspace"
    ws_dir.mkdir(parents=True, exist_ok=True)
    return ws_dir


def main():
    """Main entry point for EasyBot system."""
    global WORKSPACE, MODEL_PROVIDER, CONNECTOR
    
    parser = argparse.ArgumentParser(
        description="EasyBot - Agent Builder System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate or repair an agent:
    python -m system.main --requirement "Create a Python helper agent" --agent helper_agent
  
  Read an agent's markdown file:
    python -m system.main --read-markdown helper_agent
  
  List markdown files for all agents:
    python -m system.main --list-markdowns
  
  Interactive mode:
    python -m system.main --interactive
  
  List generated agents:
    python -m system.main --list-agents
  
  Create a reusable skill:
    python -m system.main --create-skill "example skill" --description "A reusable skill."
    
  Create a reusable tool:
    python -m system.main --create-tool "example tool" --description "A reusable tool."
  
  Start conversation with agent:
    python -m system.main --converse --agent greeting_agent
  
  Use MarkdownEngine class in your code:
    from system.markdown_engine import MarkdownEngine
    from pathlib import Path

    engine = MarkdownEngine(Path("workspace"))
    actions = engine.list_actions("greeting_agent")
    tasks = engine.list_tasks("calculator")
    code_blocks = engine.list_code_blocks("python_runner")
    
    # Search for commands
    results = engine.search_commands("calculator", "python")
    
    # Get agent manifest
    manifest = engine.generate_agent_manifest("bridge_agent")
    
    # Execute command
    result = engine.execute_command("greeting_agent", "Greet the user")
    
    # Execute all actions
    result = engine.execute_all_actions("bridge_agent")

        """
    )
    
    parser.add_argument(
        "--requirement", 
        type=str,
        help="User requirement or prompt for agent generation"
    )
    parser.add_argument(
        "--agent",
        type=str,
        help="Name of the agent to generate, repair, or converse with"
    )
    parser.add_argument(
        "--converse",
        action="store_true",
        help="Start a conversation with the agent (requires --agent)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive terminal mode"
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List all generated agents"
    )
    parser.add_argument(
        "--create-skill",
        type=str,
        help="Description for creating a new skill"
    )
    parser.add_argument(
        "--skill-name",
        type=str,
        help="Name for the new skill"
    )
    parser.add_argument(
        "--create-tool",
        type=str,
        help="Description for creating a new tool"
    )
    parser.add_argument(
        "--tool-name",
        type=str,
        help="Name for the new tool"
    )
    parser.add_argument(
        "--read-markdown",
        type=str,
        default=None,
        help="Read markdown content from agent"
    )
    parser.add_argument(
        "--list-markdowns",
        action="store_true",
        help="List markdown files for all agents"
    )
    parser.add_argument(
        "--read-all-markdowns",
        action="store_true",
        help="Read and display markdown files for all agents"
    )
    parser.add_argument(
        "--actions",
        type=str,
        default=None,
        help="Show actions from markdown"
    )
    parser.add_argument(
        "--tasks",
        type=str,
        default=None,
        help="Show tasks from markdown"
    )
    parser.add_argument(
        "--code-blocks",
        type=str,
        default=None,
        help="Show code blocks from markdown"
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Display full markdown content"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute all actions from markdown"
    )
    parser.add_argument(
        "--message",
        type=str,
        default=None,
        help="Send a message to agent"
    )
    
    args = parser.parse_args()
    
    if args.list_agents:
        # List all generated agents
        agent_dir = _get_workspace_dir() / "agent"
        if not agent_dir.exists():
            print("\nNo agents found in workspace/agent/")
            return 0
            
        agents = [d.name for d in agent_dir.iterdir() if d.is_dir()]
        if agents:
            print("\nGenerated Agents:")
            print("=" * 50)
            for agent in sorted(agents):
                agent_path = agent_dir / agent
                files = [f.name for f in agent_path.iterdir() if f.is_file()]
                print(f"  {agent}/")
                print(f"    Files: {', '.join(files)}")
            print(f"\nTotal: {len(agents)} agents")
        else:
            print("\nNo agents found in workspace/agent/")
        return 0
    
    if args.interactive:
        # Interactive mode
        messenger = Messager()
        print("\n🤖 EasyBot Agent Builder")
        print("=" * 50)
        print("Type your requirements to create agents...\n")
        
        # 询问 LLM 信息
        print("📦 LLM Configuration")
        print("-" * 50)
        print("LLM Setup:")
        print("  - /model provider:model_manufacturer/model_name")
        print("    Example: /model siliconlab:deepseek/deepseek-v4-flash")
        print("    Providers: openai, anthropic, ollama, siliconlab,local,deepseek")
        print()
        model_input = input(">").strip()
        
        # 解析模型输入
        if model_input.startswith("/model "):
            model_str = model_input[7:]  # 去掉 "/model "
            if ":" in model_str:
                provider, model_name = model_str.split(":", 1)
                model_provider = provider.strip().lower()
            else:
                model_provider = model_str.strip().lower()
        else:
            model_provider = model_input.lower() or "openai"
        
        # 初始化全局变量
        init_globals(model_provider=model_provider)
        print(f"Using LLM: {model_provider}\n")
        
        while True:
            try:
                prompt = input("Agent requirement (or 'exit' to quit): ").strip()
                if prompt.lower() == "exit":
                    break
                print("\n" + "-" * 50)
                
                creator = AgentCreator()
                # 从需求中提取 agent 名称（取前几个单词）
                import re
                name_parts = re.sub(r'[^\w\s]', '', prompt).split()[:3]
                agent_name = "_".join(name_parts).lower() or "new_agent"
                # 创建 agent
                agent, errors = creator.create_agent(agent_name, prompt)
                if errors:
                    print(f"\n⚠️ 警告: {errors}")
                print(f"\n✅ Agent '{agent_name}' created successfully!")
                from system import MODEL_PROVIDER as CURRENT_MODEL
                print(f"   Using LLM: {CURRENT_MODEL}")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue
        
        print("\n👋 Goodbye!")
        return 0
    
    if args.read_markdown:
        # Read markdown from agent using MarkdownEngine
        engine = MarkdownEngine(_get_workspace_dir())
        result = engine.read_markdown(args.read_markdown)
        
        if result["success"]:
            print(f"\n✅ Successfully read markdown from '{result['agent_name']}'")
            actions = [i.content for i in result["instructions"] if i.type == "action"]
            tasks = [i.content for i in result["instructions"] if i.type == "task"]
            print(f"Actions found: {len(actions)}")
            print(f"Tasks found: {len(tasks)}")
        else:
            print(f"❌ Error reading markdown: {result.get('error')}")
        return 1
    
    if args.read_all_markdowns:
        # Read all markdown files using MarkdownEngine
        engine = MarkdownEngine(_get_workspace_dir())
        agents = engine.list_agents()
        
        if not agents:
            print("No agents found.")
            return 0
        
        print("Markdown Files for All Agents:")
        print("=" * 50)
        
        for agent_name in agents:
            agent_path = _get_workspace_dir() / "agent" / agent_name
            md_path = agent_path / "agent.md"
            
            if md_path.exists():
                try:
                    with open(md_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    print(f"\n{'=' * 50}")
                    print(f"📄 {agent_name}/agent.md")
                    print('=' * 50)
                    print(content)
                except Exception as e:
                    print(f"❌ Error reading {agent_name}/agent.md: {e}")
        print("=" * 50)
        print(f"Total: {len(agents)} agents")
        return 0
    
    if args.list_markdowns:
        # List markdown for all agents using MarkdownEngine
        engine = MarkdownEngine(_get_workspace_dir())
        agents = engine.list_agents()
        
        if not agents:
            print("No agents found.")
            return 0
        
        print("Markdown Files for All Agents:")
        print("=" * 50)
        
        for agent_name in agents:
            agent_path = _get_workspace_dir() / "agent" / agent_name
            md_path = agent_path / "agent.md"
            
            if md_path.exists():
                print(f"✅ {agent_name}/")
                print(f"   agent.md - {md_path.stat().st_size} bytes")
            else:
                print(f"❌ {agent_name}/")
                print(f"   agent.md - Missing")
        
        print("=" * 50)
        print(f"Total: {len(agents)} agents")
        return 0
    
    # New markdown command features
    if args.actions and args.agent:
        # Show actions from markdown
        engine = MarkdownEngine(_get_workspace_dir())
        actions = engine.list_actions(args.agent)
        
        if actions:
            print(f"\n📋 Actions ({len(actions)}):")
            for i, action in enumerate(actions, 1):
                print(f"  {i}. {action}")
        else:
            print(f"❌ No actions found for {args.agent}")
            return 1
    
    elif args.tasks and args.agent:
        # Show tasks from markdown
        engine = MarkdownEngine(_get_workspace_dir())
        tasks = engine.list_tasks(args.agent)
        
        if tasks:
            print(f"\n📋 Tasks ({len(tasks)}):")
            for i, task in enumerate(tasks, 1):
                print(f"  {i}. {task}")
        else:
            print(f"❌ No tasks found for {args.agent}")
            return 1
    
    elif args.code_blocks and args.agent:
        # Show code blocks from markdown
        engine = MarkdownEngine(_get_workspace_dir())
        code_blocks = engine.list_code_blocks(args.agent)
        
        if code_blocks:
            print(f"\n📋 Code Blocks ({len(code_blocks)}):")
            for i, code in enumerate(code_blocks, 1):
                print(f"  {i}. ```")
                print(code)
                print("```")
        else:
            print(f"❌ No code blocks found for {args.agent}")
            return 1
    
    elif args.display:
        # Display full markdown content
        engine = MarkdownEngine(_get_workspace_dir())
        markdown_content = engine.get_full_markdown(args.agent)
        
        if markdown_content:
            print(f"\n{'=' * 50}")
            print(f"📄 {args.agent}/agent.md")
            print('=' * 50)
            print(markdown_content)
            print('=' * 50)
        else:
            print(f"❌ No markdown found for {args.agent}")
            return 1
    
    elif args.execute and args.agent:
        # Execute all actions
        engine = MarkdownEngine(_get_workspace_dir())
        success = engine.execute_all_actions(args.agent)
        if success:
            print(f"✅ All actions executed successfully for {args.agent}")
        else:
            print(f"❌ Some actions failed for {args.agent}")
            return 1
    
   # Conversation mode with message support
    if args.converse and args.agent:
        # Start conversation with agent
        try:
            conv = create_conversation(args.agent, _get_workspace_dir())
            print(f"\n🤖 Starting conversation with {args.agent}...")
            print("=" * 50)
            
            # Show available actions
            actions = conv.get_available_actions()
            print(f"Available actions ({len(actions)}):")
            for i, action in enumerate(actions, 1):
                print(f"  {i}. {action}")
            print("=" * 50)
            print("\nType your message to start conversation...")
            
            # Simple conversation loop
            while True:
                user_input = input("> ").strip()
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\n👋 Goodbye!")
                    break
                if not user_input:
                    continue
                
                # Get response
                response = conv.handle_user_input(user_input)
                
                print(f"\n--- Response from {args.agent} ---")
                print(response["response"])
                print(f"[Actions taken: {', '.join(response.get('actions_taken', [])) or 'None'}]")
                print("-" * 50)
                
        except Exception as e:
            print(f"❌ Error starting conversation: {e}")
            return 1
    
    # Direct message handling
    elif args.message:
        # Send message via WeChat
        try:
            message_handler = MessageRouter()
            message_handler.selected_platform = "wechat"
            
            if message_handler.send_message(args.message, "wechat"):
                print("✅ Message sent to WeChat!")
            else:
                print("❌ Failed to send message")
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return 1
    
    # Generate/repair agent
    if args.requirement and args.agent:
        print(f"Processing requirement: {args.requirement}")
        print(f"Agent name: {args.agent}")
        
        try:
            creator = AgentCreator()
            agent = creator.create_agent(args.requirement)
            print(f"✅ Agent '{args.agent}' created successfully!")
            
            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    # Create skill
    if args.create_skill and args.skill_name:
        # Create skill
        skill_path = _get_workspace_dir() / "skill" / args.skill_name
        skill_path.mkdir(parents=True, exist_ok=True)
        
        # Check if directory was created successfully
        if not skill_path.exists():
            print(f"❌ Error: Could not create directory {skill_path}")
            return 1
        
        skill_py_content = f'''#!/usr/bin/env python3
"""{args.create_skill}"""

class {args.skill_name.replace("_", "")}:
    """{args.create_skill}"""
    
    def execute(self, **kwargs):
        """Execute the skill."""
        print(f"Executing {args.skill_name}...")
        return f'{{"status": "success", "skill": {args.skill_name}}}'

if __name__ == "__main__":
    from easybot import Skill
    import sys
    skill = Skill()
    skill.execute()
'''
        with open(skill_path / "skill.py", "w") as f:
            f.write(skill_py_content)
        
        skill_md = f"""# {args.skill_name}

**Description**: {args.create_skill}

## Usage

```python
from easybot import Skill

skill = Skill()
result = skill.execute()
print(result)
```

## Requirements

- Python 3.10+
- EasyBot system
"""
        with open(skill_path / "skill.md", "w") as f:
            f.write(skill_md)
        
        print(f"✅ Skill '{args.skill_name}' created successfully!")
        return 0
    
    # Create tool
    if args.create_tool and args.tool_name:
        # Create tool
        tool_path = _get_workspace_dir() / "tool" / args.tool_name
        tool_path.mkdir(parents=True, exist_ok=True)
        
        tool_py_content = f'''#!/usr/bin/env python3
"""{args.create_tool}"""

class {args.tool_name.replace("_", "")}:
    """{args.create_tool}"""
    
    def execute(self, **kwargs):
        """Execute the tool."""
        print(f"Executing {args.tool_name}...")
        return f'{{"status": "success", "tool": {args.tool_name}}}'

if __name__ == "__main__":
    from easybot import Tool
    import sys
    tool = Tool()
    tool.execute()
'''
        with open(tool_path / "tool.py", "w") as f:
            f.write(tool_py_content)
        
        tool_md = f"""# {args.tool_name}

**Description**: {args.create_tool}

## Usage

```python
from easybot import Tool

tool = Tool()
result = tool.execute()
print(result)
```

## Requirements

- Python 3.10+
- EasyBot system
"""
        with open(tool_path / "tool.md", "w") as f:
            f.write(tool_md)
        
        print(f"✅ Tool '{args.tool_name}' created successfully!")
        return 0
    
    # No specific command given
    if args.message:
        messenger = Messager()
        msg = messenger.receive(args.message, channel="cli", sender_id="user")
        _, response = messenger.route(msg)
        print(response)
        return 0
    
    print("EasyBot - No command specified. Use --help for usage information.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
