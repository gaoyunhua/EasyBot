"""
Agent Messager — 消息入口

职责：
1. 接收各通道的消息（CLI、WeChat 等）
2. 解释消息意图
3. 路由到对应的 Agent
4. 处理最简单的用户命令（/help、/list、/status）
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class MessageChannel(str, Enum):
    CLI = "cli"
    WECHAT = "wechat"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"
    WEB = "web"


class MessageType(str, Enum):
    COMMAND = "command"          # 系统命令: /help, /list
    DIRECT_AGENT = "agent"       # @AgentName 消息
    BROADCAST = "broadcast"      # 非定向消息
    SYSTEM = "system"            # 系统内部消息


@dataclass
class Message:
    """统一消息格式"""
    text: str
    channel: MessageChannel
    sender_id: str
    sender_name: str = ""
    conversation_id: str = ""
    timestamp: str = ""
    raw: Any = None
    
    # 解析后字段
    msg_type: Optional[MessageType] = None
    target_agent: Optional[str] = None
    command: Optional[str] = None
    command_args: List[str] = field(default_factory=list)


class Messager:
    """
    Agent Messager
    
    接收消息 → 解释意图 → 路由到对应 Agent
    """
    
    def __init__(self, agents: Dict[str, Any] = None):
        self.agents = agents or {}
        self._command_handlers = {}
        self._register_default_commands()
    
    def _register_default_commands(self):
        from .commands import register_default_commands
        register_default_commands(self)
    
    def register_agent(self, name: str, agent_instance: Any):
        self.agents[name] = agent_instance
    
    def register_command(self, cmd: str, handler, description: str = ""):
        self._command_handlers[cmd] = {
            "handler": handler,
            "description": description
        }
    
    def receive(self, text: str, channel: str = "cli",
                sender_id: str = "", sender_name: str = "",
                conversation_id: str = "", raw=None) -> Message:
        """接收并解释一条消息"""
        msg = Message(
            text=text,
            channel=MessageChannel(channel) if isinstance(channel, str) else channel,
            sender_id=sender_id,
            sender_name=sender_name,
            conversation_id=conversation_id,
            raw=raw
        )
        self._interpret(msg)
        return msg
    
    def _interpret(self, msg: Message):
        """解释消息意图"""
        text = msg.text.strip()
        
        # 1. 系统命令: /xxx
        if text.startswith("/"):
            parts = text[1:].split()
            msg.msg_type = MessageType.COMMAND
            msg.command = parts[0].lower()
            msg.command_args = parts[1:]
            return
        
        # 2. @AgentName 定向消息
        agent_match = re.match(r'@(\w+)\s*(.*)', text)
        if agent_match:
            msg.msg_type = MessageType.DIRECT_AGENT
            msg.target_agent = agent_match.group(1)
            msg.text = agent_match.group(2).strip()
            return
        
        # 3. 有明确上下文 → 路由到当前活跃 Agent
        # 调用方需在 conversation_id 上维护状态
        # 此处返回 broadcast，由调用方决定
        
        # 4. 广播
        msg.msg_type = MessageType.BROADCAST
    
    def route(self, msg: Message) -> Tuple[Any, str]:
        """
        路由消息到目标处理方
        返回 (handler, response_text)
        """
        if msg.msg_type == MessageType.COMMAND:
            return self._handle_command(msg)
        
        if msg.msg_type == MessageType.DIRECT_AGENT:
            return self._route_to_agent(msg)
        
        # BROADCAST → 尝试智能路由
        return self._route_broadcast(msg)
    
    def _handle_command(self, msg: Message) -> Tuple[Any, str]:
        cmd = msg.command
        handler_info = self._command_handlers.get(cmd)
        if handler_info:
            result = handler_info["handler"](msg.command_args, msg)
            return None, result
        return None, f"未知命令: /{cmd}。输入 /help 查看可用命令。"
    
    def _route_to_agent(self, msg: Message) -> Tuple[Any, str]:
        agent = self.agents.get(msg.target_agent)
        if not agent:
            available = ", ".join(self.agents.keys())
            return None, f"找不到 Agent @{msg.target_agent}。可用: {available}"
        
        # 调用 Agent 处理消息（返回 agent + 响应）
        # Agent 需要实现 process() 方法
        response = agent.process(msg) if hasattr(agent, 'process') else f"Agent @{msg.target_agent} 收到: {msg.text}"
        return agent, response
    
    def _route_broadcast(self, msg: Message) -> Tuple[Any, str]:
        """广播消息 — 默认路由到第一个活跃 Agent 或返回未处理"""
        for name, agent in self.agents.items():
            if getattr(agent, 'is_active', False):
                response = agent.process(msg) if hasattr(agent, 'process') else None
                if response:
                    return agent, response
        return None, f"{msg.text}"
    
    def run_cli(self):
        """CLI 交互模式"""
        print("🤖 EasyBot Messager CLI")
        print("输入消息，或用 @AgentName 定向到特定 Agent")
        print("输入 /help 查看命令，/quit 退出\n")
        
        while True:
            try:
                text = input("> ").strip()
                if not text:
                    continue
                if text == "/quit" or text == "/exit":
                    break
                
                msg = self.receive(text, channel="cli", sender_id="user")
                _, response = self.route(msg)
                print(response)
                print()
            except (KeyboardInterrupt, EOFError):
                print()
                break
