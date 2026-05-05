# EasyBot - Agent Builder System

A lightweight Python system for generating and managing simple agent folders from user requirements.

## Overview

- `system/` contains the orchestrator and immutable system components.
- `workspace/` stores generated artifacts and reusable assets.
- New agents are generated into `workspace/agent/<agent_name>/`.
- Each generated agent folder is expected to contain:
  - `main.py`
  - `agent.md`
  - `agent_requirement.txt`
  - `__init__.py`

## How it works

1. `system/main.py` accepts a requirement or user prompt.
2. `system/messager/messager.py` turns the prompt into a requirement and asks `AgentCaller` to resolve it.
3. `system/agent_caller/` searches for an existing agent and repairs it if files are missing.
4. `system/builder/builder.py` creates an agent folder, a starter script, markdown documentation, and a requirement manifest.
5. `system/tester/tester.py` validates the generated folder and attempts to import and execute the agent's `main()` entrypoint.

## Quick start

From the repository root:

```bash
python -m system.main --help
```

Generate or repair an agent:

```bash





```

Read an agent's markdown file:

```bash
python -m system.main --read-markdown helper_agent
```

List all agents' markdown files:

```bash
python -m system.main --list-markdowns
```

Read and display all agents' markdown files:

```bash
python -m system.main --read-all-markdowns
```

Show actions from a specific agent:

```bash
python -m system.main --actions greeting_agent
```

Show tasks from a specific agent:

```bash
python -m system.main --tasks calculator
```

Show code blocks from a specific agent:

```bash
python -m system.main --code-blocks python_runner
```

Search for commands in an agent:

```bash
python -m system.main --search "python" calculator
```

Display full markdown content:

```bash
python -m system.main --display quant_agent
```

Execute all actions from a specific agent:

```bash
python -m system.main --execute bridge_agent
```

Generate agent manifest:

```bash
python -m system.main --manifest bridge_agent
```

Start the terminal-based messenger assistant:

```bash
python -m system.main --interactive
```

Or run with no arguments to start the terminal assistant by default:

```bash
python -m system.main
```

List generated agents:

```bash
python -m system.main --list-agents
```

Create a reusable workspace skill:

```bash
python -m system.main --create-skill "example skill" --skill-name "example_skill"
```

Create a reusable workspace tool:

```bash
python -m system.main --create-tool "example tool" --tool-name "example_tool"
```

## Developer notes

- Run commands from the repository root so Python can resolve `system` and `workspace` packages.
- Existing generated agents are preserved; new files are created only when missing.
- `pyproject.toml` defines the project metadata and a console entry point if installed.
- Uses system Python (no virtual environment required).

## Directory structure

```
EasyBot/
├── README.md
├── pyproject.toml
├── system/
│   ├── __init__.py
│   ├── main.py
│   ├── caller/
│   │   ├── __init__.py
│   │   └── caller.py
│   ├── creator/
│   │   ├── __init__.py
│   │   ├── creator.py
│   │   ├── downloader/
│   │   │   ├── __init__.py
│   │   │   ├── github_downloader.py
│   │   │   ├── local_loader.py
│   │   │   └── url_downloader.py
│   │   ├── importer/
│   │   │   ├── __init__.py
│   │   │   └── importer.py
│   │   ├── runner/
│   │   │   ├── __init__.py
│   │   │   └── runner.py
│   │   └── saver/
│   │       ├── __init__.py
│   │       └── saver.py
│   ├── markdown_engine/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── markdown_engine.py
│   │   ├── agent_conversation.py
│   │   └── message_handler/
│   │       ├── __init__.py
│   │       └── message_handler.py
│   ├── messager/
│   │   ├── __init__.py
│   │   ├── messager.py
│   │   └── commands.py
│   ├── tester/
│   │   ├── __init__.py
│   │   └── tester.py
│   └── models/
│       ├── __init__.py
│       └── agent.py
└── workspace/
    ├── agent/
    │   ├── calculator/
    │   │   └── tools/
    │   ├── csv_processor/
    │   ├── python_runner/
    │   ├── data_analyst/
    │   ├── bridge_agent/
    │   └── quant_agent/
    ├── skill/
    │   └── data_processor/
    └── tool/
        └── file_processor/
```

### tester/

Validates generated agents.

- `Tester.run_agent()`: Imports and executes agent's main function

### markdown\_engine/

Provides a unified command execution system for agents based on their markdown files.

- `MarkdownEngine`: Core class for reading and parsing markdown
  - `read_markdown(agent_name)`: Read and parse an agent's markdown file
  - `list_actions(agent_name)`: List all actions from markdown
  - `list_tasks(agent_name)`: List all tasks from markdown
  - `list_code_blocks(agent_name)`: List all code blocks from markdown
  - `get_full_markdown(agent_name)`: Get raw markdown content
  - `execute_action(agent_name, action)`: Execute a specific action
  - `execute_all_actions(agent_name)`: Execute all actions

## Components

### main.py

Main entry point with CLI interface supporting:

- `--requirement <desc> --agent <name>`: Generate/repair an agent
- `--interactive`: Interactive terminal mode
- `--list-agents`: List all agents
- `--create-skill <desc> --skill-name <name>`: Create a skill
- `--create-tool <desc> --tool-name <name>`: Create a tool
- `--read-markdown <agent>`: Read markdown content from agent
- `--list-markdowns`: List markdown files for all agents
- `--read-all-markdowns`: Read and display markdown files for all agents
- `--actions <agent>`: Show actions from markdown
- `--tasks <agent>`: Show tasks from markdown
- `--code-blocks <agent>`: Show code blocks from markdown
- `--search <query> <agent>`: Search for commands
- `--display`: Display full markdown content
- `--execute`: Execute all actions from markdown
- `--manifest`: Generate agent manifest

### markdown\_engine/

**The core of the EasyBot system - Unified Command Execution Engine**

- `MarkdownEngine`: Core class for reading, parsing, and executing commands
  - `read_markdown(agent_name)`: Read and parse an agent's markdown file
  - `list_actions(agent_name)`: List all actions from markdown
  - `list_tasks(agent_name)`: List all tasks from markdown
  - `list_code_blocks(agent_name)`: List all code blocks from markdown
  - `get_full_markdown(agent_name)`: Get raw markdown content
  - `get_command_breakdown(agent_name)`: Get command type breakdown
  - `execute_command(agent_name, command)`: Execute a specific command
  - `execute_all_actions(agent_name)`: Execute all actions
  - `search_commands(agent_name, query)`: Search for commands
  - `generate_agent_manifest(agent_name)`: Generate agent capabilities manifest
- `MarkdownCommandExecutor`: CLI helper for markdown commands
- `CommandType`: Enum for command types (ACTION, TASK, CODE, INFO, STEP, RULE, PARAM, META, WORKFLOW)
- `CommandDefinition`: Dataclass for command metadata
- `CommandContext`: Context for command execution

### agent\_caller/

Handles searching for and repairing existing agents.

- `SystemAgentCaller.resolve_request()`: Parses user prompts and extracts agent names
- `SystemAgentCaller.repair_agent()`: Generates missing files for existing agents
- `SystemAgentCaller.check_agent_files()`: Validates agent folder completeness

### builder/

Creates new agent folders with starter files.

- `Builder.create_agent()`: Generates minimal agent structure

### messager/

Parses user input and converts it into structured requirements.

### tester/

Validates generated agents.

- `Tester.run_agent()`: Imports and executes agent's main function

## License

MIT License
