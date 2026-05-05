# Markdown Engine - Feature Summary

## Overview
The **Markdown Engine** is the core command execution system for the EasyBot Agent Builder. It provides a unified way to define, parse, and execute agent commands from markdown files with support for multiple command types, priority handling, and comprehensive workflow management.

## Key Features

### 1. Command Type Support
- **Actions**: User-facing actions that agents can perform
- **Tasks**: Internal tasks and steps
- **Code**: Code blocks and snippets
- **Info**: Informational content
- **Step**: Sequential steps in workflows
- **Rule**: Rules and constraints
- **Param**: Parameters for actions
- **Meta**: Metadata and configuration
- **Workflow**: Complex multi-step workflows

### 2. Markdown Parsing
Supports multiple markdown formats:
- Standard list items (`-` or `*`)
- YAML front matter for metadata
- JSON code blocks for structured data
- Custom command blocks (`## Command: name`)
- Task sections (`## Task:`)
- Info sections (`## Info:`)
- Parameter definitions
- Tags and enable/disable markers

### 3. Command Execution
- Execute specific commands by name
- Execute all actions in sequence
- Context-aware execution with state management
- Error handling and recovery
- History tracking for execution

### 4. Search and Discovery
- Search commands by content, name, or description
- Filter by command type
- Tag-based filtering
- Source file and line number tracking

### 5. Agent Manifest Generation
- Comprehensive agent capability documentation
- Command type breakdown
- Capability metadata
- Timestamps and metadata
- Export-ready JSON format

### 6. CLI Interface
Full command-line interface for:
- Listing actions from agents
- Displaying tasks
- Showing code blocks
- Searching for commands
- Displaying full markdown content
- Generating manifests
- Executing all actions

## API Usage

### Basic Operations

```python
from system.markdown_engine import MarkdownEngine
from pathlib import Path

# Initialize
engine = MarkdownEngine(Path("/mnt/d/gyh/Projects/TRAE/EasyBot/workspace"))

# List all agents
agents = engine.list_agents()

# Read and parse an agent's markdown
result = engine.read_markdown("greeting_agent")
print(f"Found {len(result['instructions'])} instructions")

# Get actions
actions = engine.list_actions("greeting_agent")
print(actions)  # ['Greet the user', 'Ask how I can help', ...]

# Get tasks
tasks = engine.list_tasks("calculator")

# Get code blocks
code_blocks = engine.list_code_blocks("python_runner")

# Get command breakdown by type
breakdown = engine.get_command_breakdown("calculator")
print(breakdown)  # {'action': 3, 'code': 1, 'task': 2}

# Search for commands
search_results = engine.search_commands("calculator", "python")
print(f"Found {len(search_results)} matches")

# Get agent manifest
manifest = engine.generate_agent_manifest("bridge_agent")
print(json.dumps(manifest, indent=2))

# Get total command count
count = engine.get_command_count("greeting_agent")
```

### Command Execution

```python
# Execute a specific command
result = engine.execute_command("greeting_agent", "Greet the user")
print(result)  # {'success': True, 'command': 'Greet the user', ...}

# Execute all actions
exec_result = engine.execute_all_actions("bridge_agent")
print(exec_result)  # {'success': True, 'agent': 'bridge_agent', ...}

# Create custom command context
context = CommandContext(
    agent_name="calculator",
    workspace=Path("/mnt/d/gyh/Projects/TRAE/EasyBot/workspace")
)
result = engine.execute_command("calculator", "Add numbers", context=context)
```

### Advanced Features

```python
# Register custom commands
engine.register_command(
    agent_name="custom_agent",
    command_type=CommandType.ACTION,
    name="Custom Action",
    description="A custom action",
    parameters={"param1": "value"},
    enabled=True,
    priority=10
)

# Execute with context
result = engine.execute_command(
    "calculator", 
    "Custom Action",
    context=CommandContext(agent_name="calculator")
)

# Get full markdown content
full_md = engine.get_full_markdown("greeting_agent")

# Search with filters
matches = engine.search_commands("calculator", "python", [CommandType.CODE])
```

## CLI Usage

```bash
# List actions from an agent
python3 -m system.markdown_engine --agent greeting_agent --actions

# List tasks from an agent
python3 -m system.markdown_engine --agent calculator --tasks

# List code blocks
python3 -m system.markdown_engine --agent python_runner --code-blocks

# Search for commands
python3 -m system.markdown_engine --agent calculator --search "python"

# Display full markdown
python3 -m system.markdown_engine --agent greeting_agent --display

# Generate manifest
python3 -m system.markdown_engine --agent greeting_agent --manifest

# Execute all actions
python3 -m system.main --execute bridge_agent

# Read markdown content
python3 -m system.main --read-markdown greeting_agent

# List all markdown files
python3 -m system.main --list-markdowns

# Read all markdowns
python3 -m system.main --read-all-markdowns
```

## Markdown Format Example

```markdown
# Calculator Agent

**Description**: A calculator agent for mathematical operations

---

## Overview

- Perform basic arithmetic
- Handle complex expressions
- Support multiple number formats

---

## Actions

- Add two numbers
- Subtract two numbers
- Multiply two numbers
- Divide two numbers
- Calculate square root
- Calculate factorial
- Compute power

## Tasks

- Parse input expression
- Validate numbers
- Execute calculation
- Format output

## Usage

```python
# Example usage
result = calculator.add(5, 3)
```

---

## Tags

math
calculator
arithmetic

## Parameters

- precision: decimal places (default: 2)
- mode: basic, advanced (default: basic)
- timeout: execution timeout in seconds (default: 30)
```

## File Structure

```
system/markdown_engine/
├── __init__.py          # Package exports
├── __main__.py          # CLI entry point
├── markdown_engine.py   # Core MarkdownEngine class
└── FEATURES.md          # This file
```

## Version

**Version**: 2.0.0  
**Author**: EasyBot System  
**License**: Proprietary
