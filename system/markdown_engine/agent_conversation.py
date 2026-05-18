"""
Agent Conversation Engine - Interactive markdown-based agent communication
=====================================================

This module enables agents to have natural conversations based on their
markdown files. It combines static commands with LLM-powered responses.

Version: 1.0.0
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from system.markdown_engine import (
    MarkdownEngine,
    CommandType,
    CommandDefinition,
    CommandContext
)


@dataclass
class ConversationState:
    """State for agent conversation."""
    agent_name: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    current_action: str = ""
    current_task: str = ""
    conversation_history: Dict[str, str] = field(default_factory=dict)
    active_commands: List[str] = field(default_factory=list)
    user_variables: Dict[str, str] = field(default_factory=dict)


class AgentConversation:
    """
    Enables interactive conversation with agents through their markdown files.
    
    This class provides the ability for users to talk to agents, where the agent
    reads its markdown, performs actions, and responds based on the conversation
    context.
    """
    
    def __init__(self, agent_name: str = None, workspace: Path = None):
        """Initialize the conversation engine.
        
        Args:
            agent_name: Name of the agent to converse with. If None, prompts user.
            workspace: Optional workspace path
        """
        self.engine = MarkdownEngine(workspace or Path(__file__).resolve().parent.parent.parent / "workspace")
        self.agent_name = agent_name
        self.state = ConversationState(agent_name=agent_name)
        self.conversation_log = []
        
        if not agent_name:
            self.agent_name = self._prompt_for_agent()
    
    def _prompt_for_agent(self) -> str:
        """Prompt user for agent name."""
        agents = self.engine.list_agents()
        if not agents:
            return "default"
        print("\nAvailable agents:")
        for i, agent in enumerate(agents, 1):
            print(f"  {i}. {agent}")
        choice = input("Enter agent number (or name): ").strip()
        if choice.isdigit():
            return agents[int(choice) - 1]
        return choice
    
    def reset_conversation(self):
        """Reset conversation state."""
        self.state.messages = []
        self.state.current_action = ""
        self.state.current_task = ""
        self.state.conversation_history = {}
        self.state.active_commands = []
        self.state.user_variables = {}
        self.state.messages.append({
            "role": "system",
            "content": f"New conversation started with {self.agent_name}",
            "timestamp": datetime.now().isoformat()
        })
    
    def get_markdown_content(self) -> str:
        """Get the agent's markdown content."""
        return self.engine.get_full_markdown(self.agent_name)
    
    def get_available_actions(self) -> List[str]:
        """Get list of available actions."""
        return self.engine.list_actions(self.agent_name)
    
    def get_available_tasks(self) -> List[str]:
        """Get list of available tasks."""
        return self.engine.list_tasks(self.agent_name)
    
    def handle_user_input(self, user_message: str) -> Dict[str, Any]:
        """Process user input and generate response.
        
        Args:
            user_message: User's input message
            
        Returns:
            Response dictionary with agent's reply and actions taken
        """
        self.state.messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        response = {
            "agent": self.agent_name,
            "user_message": user_message,
            "response": "",
            "actions_taken": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Step 1: Extract commands from user input
        commands = self._extract_commands(user_message)
        
        if commands:
            # Execute commands first
            for cmd in commands:
                self.state.active_commands.append(cmd)
                result = self._execute_command(cmd)
                self.state.messages.append({
                    "role": "assistant",
                    "content": f"Executed command: {cmd}",
                    "timestamp": datetime.now().isoformat()
                })
                if result.get("success"):
                    response["actions_taken"].append(cmd)
                    # Update context from result
                    if "context" in result:
                        self.state.context.update(result["context"].get("variables", {}))
        
        # Step 2: Generate LLM response based on markdown and conversation
        response["response"] = self._generate_llm_response(user_message)
        
        # Step 3: Update conversation history
        self.state.conversation_history[user_message] = response["response"]
        self.conversation_log.append(response)
        
        return response
    
    def _extract_commands(self, user_message: str) -> List[str]:
        """Extract commands from user message.
        
        Supports patterns like:
        - "Run <action_name>"
        - "Do <action_name>"
        - "Execute <action_name>"
        - "Show <action_name>"
        - "Help me with <action_name>"
        
        Args:
            user_message: User's message
            
        Returns:
            List of command names extracted
        """
        commands = []
        actions = self.engine.list_actions(self.agent_name)
        
        # Look for command patterns
        patterns = [
            r'(?:run|do|execute|show|help\s+with|perform)\s+([^\s,]+)',
            r'(?i)(?:go\s+to|get\s+|find\s+|search\s+|create\s+|update\s+|delete\s+)(\w+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, user_message.lower())
            for match in matches:
                match_clean = match.strip().strip("'\"")
                # Check if it's a valid action or keyword
                if match_clean.lower() not in ["help", "list", "show", "actions", "tasks", "info"]:
                    if match_clean in actions or match_clean in self.state.user_variables:
                        commands.append(match_clean)
        
        return commands
    
    def _execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command and return result.
        
        Args:
            command: Command name to execute
            
        Returns:
            Command execution result
        """
        result = self.engine.execute_command(self.agent_name, command)
        
        if not result.get("success"):
            return result
        
        # Extract variables from result
        if "context" in result:
            context = result["context"]
            if "variables" in context:
                self.state.user_variables.update(context["variables"])
        
        return result
    
    def _generate_llm_response(self, user_message: str) -> str:
        """Generate LLM-powered response based on agent's markdown.
        
        This method combines:
        1. Agent's markdown content
        2. Conversation history
        3. User variables
        4. Current context
        
        Args:
            user_message: User's original message
            
        Returns:
            Agent's response
        """
        markdown_content = self.get_markdown_content()
        actions = self.engine.list_actions(self.agent_name)
        tasks = self.engine.list_tasks(self.agent_name)
        code_blocks = self.engine.list_code_blocks(self.agent_name)
        
        # Build prompt for LLM
        prompt = self._build_llm_prompt(user_message, markdown_content, actions, tasks, code_blocks)
        
        # In a real implementation, this would call an LLM API
        # For now, we'll return a simulated response based on context
        
        return self._simulate_llm_response(prompt)
    
    def _build_llm_prompt(self, user_message: str, markdown: str, 
                         actions: List[str], tasks: List[str], 
                         code_blocks: List[str]) -> str:
        """Build a prompt for LLM to generate agent response.
        
        Args:
            user_message: User's message
            markdown: Agent's markdown content
            actions: Available actions
            tasks: Available tasks
            code_blocks: Code blocks in markdown
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are {self.agent_name}, an intelligent agent.

Your capabilities are defined in your markdown file.
You have the following actions you can perform:
{', '.join(actions) if actions else 'No actions'}

You can also help with these tasks:
{', '.join(tasks) if tasks else 'No tasks'}

Here are some code examples you can reference:
```python
{'\n'.join(code_blocks[:3]) if code_blocks else 'No code blocks'}
```

Current user message:
""" + user_message + """

Available user-defined variables:
""" + str(self.state.user_variables) + """

Conversation history (last 5 exchanges):
""" + '\n'.join(f"- {m['role']}: {m['content']}" for m in self.state.messages[-5:]) + """

Please provide a helpful, intelligent response based on your markdown file and the conversation context."""
        
        return prompt
    
    def _simulate_llm_response(self, prompt: str) -> str:
        """Simulate LLM response (replace with actual LLM call).
        
        Args:
            prompt: The prompt sent to LLM
            
        Returns:
            Simulated response
        """
        # In production, replace this with actual LLM API call
        # Example: response = llm_api.generate(prompt)
        
        # Simple heuristic-based response for demonstration
        if "help" in prompt.lower():
            return self._generate_help_response()
        elif "hello" in prompt.lower() or "hi" in prompt.lower():
            return self._generate_welcome_response()
        elif "what" in prompt.lower():
            return self._generate_info_response()
        else:
            return f"As {self.agent_name}, I understand you want to know about: {prompt[:50]}..."
    
    def _generate_help_response(self) -> str:
        """Generate help response."""
        actions = self.engine.list_actions(self.agent_name)
        tasks = self.engine.list_tasks(self.agent_name)
        
        # Build response using format() instead of f-string
        action_list = ", ".join(actions) if actions else "No actions"
        task_list = ", ".join(tasks) if tasks else "No tasks"
        
        # Use string formatting properly
        response = f"""# {self.agent_name} Help

## Available Actions ({len(actions)})
{chr(10).join(f"- {a}" for a in actions)}

## Available Tasks ({len(tasks)})
{chr(10).join(f"- {t}" for t in tasks)}

## How to Use
You can:
- Ask me questions about my capabilities
- Run specific actions: "Run <action>" for any action
- Get information about tasks
- Discuss my code examples

## Example Commands
- "Show me your actions"
- "What can you do?"
- "Run <action>" (replace with actual action name)

Feel free to ask me anything about my capabilities!"""
        
        return response
    
    def _generate_welcome_response(self) -> str:
        """Generate welcome response."""
        actions = self.engine.list_actions(self.agent_name)
        markdown = self.get_markdown_content()
        
        response = """Hello! 👋 I'm {self.agent_name}. I'm an intelligent agent with capabilities defined in my markdown file.

You can:
1. Ask me questions about what I can do
2. Run specific actions: "Run <action>" (replace <action> with an action name)
3. Get help with tasks
4. Discuss my code examples

Would you like to see my available actions or start with a specific task?"""
        
        return response.format(action="action name")
    
    def _generate_info_response(self) -> str:
        """Generate general information response."""
        return f"I can help you with various tasks. Would you like to see my available actions or work on something specific?"
    
    def set_user_variable(self, name: str, value: str):
        """Set a user variable for context.
        
        Args:
            name: Variable name
            value: Variable value
        """
        self.state.user_variables[name] = value
        return {"success": True, "variable": name, "value": value}
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation.
        
        Returns:
            Conversation summary
        """
        return {
            "agent": self.agent_name,
            "total_messages": len(self.state.messages),
            "user_messages": len([m for m in self.state.messages if m["role"] == "user"]),
            "assistant_messages": len([m for m in self.state.messages if m["role"] == "assistant"]),
            "variables": self.state.user_variables,
            "active_commands": self.state.active_commands
        }
    
    def export_conversation(self, filename: str = None) -> str:
        """Export conversation to text file.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            filename = f"conversation_{self.agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filepath = Path(filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Agent: {self.agent_name}\n")
            f.write(f"Started: {self.state.messages[0].get('timestamp', 'N/A')}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, msg in enumerate(self.state.messages, 1):
                f.write(f"\n--- Message {i} ---\n")
                f.write(f"Role: {msg['role']}\n")
                f.write(f"Content: {msg['content']}\n")
        
        return str(filepath)


def create_conversation(agent_name: str = None, workspace: Path = None) -> AgentConversation:
    """Factory function to create conversation instance.
    
    Args:
        agent_name: Name of the agent
        workspace: Optional workspace path
        
    Returns:
        AgentConversation instance
    """
    return AgentConversation(agent_name, workspace)


# Export main classes
__all__ = [
    "AgentConversation",
    "create_conversation",
    "ConversationState",
]
