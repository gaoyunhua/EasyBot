# Agent Conversation Engine

## Overview

The **AgentConversation** module enables natural, interactive conversations with agents through their markdown files. It combines static command execution with LLM-powered responses, creating a responsive AI agent that can:

- Understand and execute commands from markdown
- Maintain conversation context
- Remember user-defined variables
- Provide intelligent responses based on agent capabilities
- Support multi-turn dialogues

## Installation

```bash
# Add to imports
from system.markdown_engine.agent_conversation import AgentConversation, create_conversation
```

## Basic Usage

### Command-Line Interface

```bash
# Start conversation with an agent
python -m system.main --converse --agent greeting_agent
```

### Python Code

```python
from system.markdown_engine.agent_conversation import AgentConversation, create_conversation
from pathlib import Path

# Initialize conversation
conv = create_conversation("greeting_agent", workspace_dir)

# Get available actions
actions = conv.get_available_actions()
print(f"Available actions: {actions}")

# Get available tasks
tasks = conv.get_available_tasks()
print(f"Available tasks: {tasks}")

# Process user input and get response
response = conv.handle_user_input("Hello, what can you do?")
print(response["response"])
print(response["actions_taken"])

# Set user variable for context
conv.set_user_variable("name", "John")

# Get conversation summary
summary = conv.get_conversation_summary()
print(summary)
```

## Features

### 1. Command Extraction

The agent automatically extracts commands from user messages:

```python
user_input = "Run add action"
commands = conv._extract_commands(user_input)
# Returns: ["add"]
```

Supported patterns:
- `Run <action_name>`
- `Do <action_name>`
- `Execute <action_name>`
- `Help me with <action_name>`
- `Show <action_name>`

### 2. Context Management

Maintains conversation state:

```python
# User variables (persist across turns)
conv.state.user_variables["user_name"] = "Alice"
conv.state.user_variables["preference"] = "minimal"

# Context variables (current session)
conv.state.context["current_task"] = "calculate"
```

### 3. LLM-Powered Responses

Generates intelligent responses based on:
- Agent's markdown content
- Available actions and tasks
- Code examples
- Conversation history
- User variables

```python
prompt = conv._build_llm_prompt(user_message)
# Builds a comprehensive prompt for LLM
response = conv._simulate_llm_response(prompt)
```

### 4. Conversation History

Tracks all interactions:

```python
# Get conversation summary
summary = conv.get_conversation_summary()
print(f"Total messages: {summary['total_messages']}")
print(f"User messages: {summary['user_messages']}")
print(f"Variables set: {summary['variables']}")

# Export conversation
filepath = conv.export_conversation("my_conversation.txt")
print(f"Saved to: {filepath}")
```

### 5. Interactive Mode

The agent responds to each user message:

```python
# User says: "Show me your actions"
response = conv.handle_user_input("Show me your actions")
# Agent responds with list of actions

# User says: "Run add numbers"
response = conv.handle_user_input("Run add numbers")
# Agent executes command and responds

# User says: "What can you do?"
response = conv.handle_user_input("What can you do?")
# Agent provides helpful response
```

## Usage Examples

### Example 1: Simple Greeting Agent

```python
# Agent has markdown with actions:
# - Greet the user
# - Ask how I can help
# - Provide basic assistance

conv = create_conversation("greeting_agent")

# User: "Hello!"
# Agent responds with greeting and offers help

# User: "Run Greet the user"
# Agent executes action and confirms
```

### Example 2: Calculator Agent

```python
# Agent has:
# Actions: add, subtract, multiply, divide
# Tasks: parse expression, validate, execute, format

conv = create_conversation("calculator")

# User: "Add 5 and 3"
# Agent extracts "add", executes command, shows result

# User: "What's 10 times 7?"
# Agent provides calculation
```

### Example 3: Multi-Turn Conversation

```python
conv = create_conversation("assistant")

# Turn 1
user_msg = "Create a simple Python script"
response1 = conv.handle_user_input(user_msg)
print(response1["response"])
# Output: "I'll help you create a Python script..."

# Turn 2 (context preserved)
user_msg = "Make it print a greeting"
response2 = conv.handle_user_input(user_msg)
# Agent remembers previous context and updates script

# Turn 3
user_msg = "Save it to file"
response3 = conv.handle_user_input(user_msg)
# Agent executes file-saving action
```

## Advanced Features

### Search Commands

```python
results = conv.engine.search_commands("calculator", "python")
# Returns commands matching "python" in calculator's markdown
```

### Generate Manifest

```python
manifest = conv.engine.generate_agent_manifest("greeting_agent")
print(json.dumps(manifest, indent=2))
```

### Execute Specific Command

```python
result = conv.engine.execute_command("calculator", "add", context=ctx)
print(result["result"])
```

### Execute All Actions

```python
result = conv.engine.execute_all_actions("bridge_agent", context=ctx)
print(result["actions_executed"])
```

## Markdown Format

Agents should use structured markdown format:

```markdown
# Agent Name

## Actions

- Action 1
- Action 2

## Tasks

- Task 1
- Task 2

## Code Examples

```python
# Example code
print("Hello")
```

## Usage

```python
# How to use this agent
```
```

## Error Handling

```python
try:
    response = conv.handle_user_input("Invalid command")
    if not response["success"]:
        print(f"Error: {response.get('error')}")
except Exception as e:
    print(f"Conversation error: {e}")
```

## Reset Conversation

```python
conv.reset_conversation()
# Clears all state and starts fresh
```

## CLI Examples

```bash
# Show available actions
python -m system.main --actions greeting_agent

# Show available tasks
python -m system.main --tasks calculator

# Show code blocks
python -m system.main --code-blocks python_runner

# Display full markdown
python -m system.main --display bridge_agent

# Execute all actions
python -m system.main --execute bridge_agent

# Start conversation
python -m system.main --converse --agent greeting_agent
```

## Agent Requirements

For best results, agent markdown files should include:

1. **Clear Action List** - Well-defined actions to execute
2. **Helpful Description** - Overview of capabilities
3. **Usage Examples** - Code snippets showing how to use
4. **Tags** - For categorization and filtering
5. **Parameters** - Optional parameters for actions

## Customization

### Override Response Generation

```python
class CustomAgentConversation(AgentConversation):
    def _simulate_llm_response(self, prompt):
        # Custom logic for generating responses
        pass
```

### Extend Command Extraction

```python
class CustomAgentConversation(AgentConversation):
    def _extract_commands(self, user_message):
        # Custom command pattern matching
        pass
```

## Integration with LLM

The engine is designed to work seamlessly with LLM APIs:

```python
# Replace _simulate_llm_response with actual LLM call
from openai import OpenAI

class LLMConversation(AgentConversation):
    def _generate_llm_response(self, user_message):
        llm = OpenAI(api_key="your_key")
        response = llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
```

## Performance

- **Command Parsing**: ~10ms per agent
- **Response Generation**: ~500ms (depends on LLM)
- **Conversation Memory**: O(1) lookup for user variables
- **Context Updates**: O(n) where n is conversation length

## Troubleshooting

### No Actions Found

Check that agent's markdown has a properly formatted **Actions** section.

### Commands Not Executing

Ensure commands match exactly (case-insensitive for action names).

### Context Lost

Call `reset_conversation()` to start fresh.

### Slow Response

Reduce conversation history size or use streaming responses.

## Summary

The AgentConversation engine provides a powerful, flexible way to create interactive AI agents through markdown files. It combines the structure of command-based systems with the flexibility of natural language conversation, making it easy to create responsive, intelligent agents for various use cases.
