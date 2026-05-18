"""
Message Handler - Handle messages from CLI and WeChat
=====================================================

This module enables the agent to communicate via:
1. CLI (command line)
2. WeChat/Weixin
3. Other messaging platforms

Supports:
- Message input/output
- Message queue
- Platform-specific handlers
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from system.messager.messager import Messager


class MessageHandler(ABC):
    """Abstract base class for message handlers."""
    
    @abstractmethod
    def send_message(self, message: str, platform: str = "cli") -> bool:
        """Send a message through a platform.
        
        Args:
            message: The message content
            platform: Platform to send to (cli, wechat, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive a message from a platform.
        
        Returns:
            dict: Message data or None if no message
        """
        pass


class CLIHandler(MessageHandler):
    """CLI message handler."""
    
    def __init__(self):
        self.buffer = []
    
    def send_message(self, message: str, platform: str = "cli") -> bool:
        """Send message via CLI."""
        if platform == "cli":
            print(message)
            return True
        return False
    
    def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive message from CLI (simulated)."""
        # In interactive mode, we'll read from stdin
        return {"type": "input", "content": input("> ") if not self.buffer else self.buffer.pop(0)}


class WeChatHandler(MessageHandler):
    """WeChat message handler (stub — actual WeChat integration uses Hermes weixin platform)."""
    
    def __init__(self):
        self.messager = Messager()
        self.chat_id = None
    
    def send_message(self, message: str, platform: str = "wechat") -> bool:
        """Send message via WeChat."""
        try:
            if platform == "wechat":
                return True
        except Exception as e:
            print(f"❌ WeChat send error: {e}")
        return False
    
    def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive message from WeChat."""
        return None


class MessageQueue:
    """Message queue for processing messages."""
    
    def __init__(self, max_size: int = 100):
        self.messages: List[Dict[str, Any]] = []
        self.max_size = max_size
    
    def enqueue(self, message: Dict[str, Any]) -> bool:
        """Add message to queue.
        
        Args:
            message: Message data
            
        Returns:
            bool: True if successful
        """
        if len(self.messages) >= self.max_size:
            return False
        self.messages.append(message)
        return True
    
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """Remove and return message from queue.
        
        Returns:
            dict: Message data or None if empty
        """
        if not self.messages:
            return None
        return self.messages.pop(0)
    
    def peek(self) -> Optional[Dict[str, Any]]:
        """Return message without removing from queue.
        
        Returns:
            dict: Message data or None if empty
        """
        return self.messages[0] if self.messages else None
    
    def size(self) -> int:
        """Return number of messages in queue."""
        return len(self.messages)


class MessageRouter:
    """Route messages to appropriate handlers based on user choices."""
    
    def __init__(self):
        self.handlers: Dict[str, MessageHandler] = {
            "cli": CLIHandler(),
            "wechat": WeChatHandler()
        }
        self.message_queue = MessageQueue()
    
    def choose_platform(self) -> str:
        """Show platform choices and return selected platform.
        
        Returns:
            str: Selected platform (cli, wechat, etc.)
        """
        print("\n📱 Choose message platform:")
        print("=" * 50)
        print("1. CLI (Command Line)")
        print("2. WeChat (微信)")
        print("3. Other (Enter custom platform)")
        print("=" * 50)
        
        try:
            choice = input("Enter choice (1/2/3): ").strip()
            
            if choice == "1":
                return "cli"
            elif choice == "2":
                return "wechat"
            elif choice == "3":
                platform = input("Enter platform name: ").strip()
                self.handlers[platform] = WeChatHandler()
                return platform
            else:
                print("Invalid choice. Defaulting to CLI.")
                return "cli"
        except Exception as e:
            print(f"Error: {e}")
            return "cli"
    
    def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive message from selected platform.
        
        Returns:
            dict: Message data or None if no message
        """
        platform = self.choose_platform()
        handler = self.handlers.get(platform)
        
        if not handler:
            print(f"❌ Unknown platform: {platform}")
            return None
        
        return handler.receive_message()
    
    def send_message(self, message: str, platform: str = "cli") -> bool:
        """Send message through selected platform.
        
        Args:
            message: The message content
            platform: Platform to send to
            
        Returns:
            bool: True if successful
        """
        handler = self.handlers.get(platform)
        
        if not handler:
            print(f"❌ Handler not found for platform: {platform}")
            return False
        
        return handler.send_message(message, platform)


def handle_user_choice(message: str) -> str:
    """Handle user choice from message.
    
    Args:
        message: User's message
        
    Returns:
        str: User's choice
    """
    print("\n📝 Your message:")
    print(message)
    
    # Parse choices from message
    if "1" in message and "2" in message:
        try:
            choice = input("Choose option (1/2): ").strip()
            return choice
        except:
            return "1"
    elif "action" in message.lower():
        print("\nAvailable actions:")
        print("1. Execute action")
        print("2. Show help")
        print("3. Exit")
        try:
            choice = input("Enter choice (1/2/3): ").strip()
            return choice
        except:
            return "1"
    
    return "1"


class InteractiveMessageHandler:
    """Interactive message handler with user choices."""
    
    def __init__(self):
        self.router = MessageRouter()
        self.selected_platform = None
    
    def start_interaction(self) -> bool:
        """Start interactive message session.
        
        Returns:
            bool: True if successful
        """
        try:
            self.selected_platform = self.router.choose_platform()
            print(f"\n✅ Selected platform: {self.selected_platform}")
            print("=" * 50)
            
            # Show available actions
            self.show_available_actions()
            
            return True
        except Exception as e:
            print(f"❌ Error starting interaction: {e}")
            return False
    
    def show_available_actions(self):
        """Show available actions for the agent."""
        # This would be implemented based on agent capabilities
        print("\n🤖 Available actions:")
        print("1. Greet user")
        print("2. Show agent info")
        print("3. Help")
        print("4. Exit")
    
    def handle_message(self, user_message: str) -> str:
        """Handle user message and return response.
        
        Args:
            user_message: User's message
            
        Returns:
            str: Response message
        """
        if not user_message.strip():
            return "Please enter a message."
        
        # Route to appropriate handler
        response = self.router.send_message(user_message, self.selected_platform)
        
        if response:
            return f"Message sent to {self.selected_platform}"
        else:
            return "Failed to send message."


if __name__ == "__main__":
    # Test message handler
    print("Testing MessageHandler...")
    handler = MessageRouter()
    
    # Show choices
    print("\n📱 Choose platform:")
    print("1. CLI")
    print("2. WeChat")
    print("3. Other")
    
    choice = input("Enter choice (1/2/3): ")
    platform = handler.choose_platform()
    print(f"\n✅ Selected: {platform}")
