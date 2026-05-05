"""Markdown Engine - Unified command execution for EasyBot agents."""

from pathlib import Path
from typing import Dict, List, Optional, Any

from .markdown_engine import (
    MarkdownEngine,
    MarkdownCommandExecutor,
    CommandType,
    CommandDefinition,
    CommandContext,
)
from .agent_conversation import (
    AgentConversation,
    create_conversation,
)
from .message_handler import (
    MessageHandler,
    CLIHandler,
    WeChatHandler,
    MessageRouter,
    InteractiveMessageHandler,
)

__all__ = [
    "MarkdownEngine",
    "MarkdownCommandExecutor",
    "CommandType",
    "CommandDefinition",
    "CommandContext",
    "AgentConversation",
    "MessageAgentMarkdownEngine",
    "create_conversation",
    "MessageHandler",
    "CLIHandler",
    "WeChatHandler",
    "MessageRouter",
    "InteractiveMessageHandler",
    "MessageAgentMarkdownEngine",
]

__version__ = "2.0.0"
