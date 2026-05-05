"""Messager 默认命令注册"""

def register_default_commands(messager):
    """注册内置命令"""
    
    def cmd_help(args, msg):
        lines = ["📋 **可用命令**:\n"]
        lines.append(f"  /help         显示帮助")
        lines.append(f"  /list         列出所有 Agent")
        lines.append(f"  /status       Agent 状态")
        lines.append(f"  /activate    激活 Agent: /activate <name>")
        lines.append(f"  /deactivate   停用 Agent: /deactivate <name>")
        lines.append(f"  /import       导入新 Agent")
        lines.append(f"  /quit        退出")
        lines.append("")
        lines.append("**消息格式**:")
        lines.append(f"  @AgentName 消息内容  定向发送给指定 Agent")
        lines.append(f"  直接输入文本         广播给所有 Agent")
        return "\n".join(lines)
    
    def cmd_list(args, msg):
        if not messager.agents:
            return "暂无已注册 Agent。使用 /import 导入。"
        
        lines = ["📋 **已注册 Agent**:\n"]
        for name, agent in messager.agents.items():
            active = "🟢" if getattr(agent, 'is_active', False) else "⚪"
            desc = getattr(agent, 'description', '') or ''
            lines.append(f"  {active} **@{name}** — {desc}")
        return "\n".join(lines)
    
    def cmd_status(args, msg):
        if args:
            name = args[0]
            agent = messager.agents.get(name)
            if not agent:
                return f"找不到 Agent: {name}"
            return _agent_status(name, agent)
        
        lines = ["📊 **Agent 状态总览**:\n"]
        for name, agent in messager.agents.items():
            active = "🟢 运行中" if getattr(agent, 'is_active', False) else "⚪ 休眠"
            desc = getattr(agent, 'description', '') or ''
            phase = getattr(agent, 'phase', 'unknown')
            lines.append(f"  **@{name}** — {active} [{phase}] — {desc}")
        return "\n".join(lines)
    
    def _agent_status(name, agent):
        lines = [f"📊 **@{name}** 状态\n"]
        lines.append(f"  描述: {getattr(agent, 'description', '无')}")
        lines.append(f"  阶段: {getattr(agent, 'phase', 'unknown')}")
        lines.append(f"  活跃: {'是' if getattr(agent, 'is_active', False) else '否'}")
        skills = getattr(agent, 'skills', [])
        tools = getattr(agent, 'tools', [])
        lines.append(f"  Skills: {len(skills)} 个")
        lines.append(f"  Tools: {len(tools)} 个")
        last_called = getattr(agent, 'last_called', '')
        if last_called:
            lines.append(f"  上次调用: {last_called}")
        return "\n".join(lines)
    
    def cmd_activate(args, msg):
        if not args:
            return "用法: /activate <AgentName>"
        name = args[0]
        agent = messager.agents.get(name)
        if not agent:
            return f"找不到 Agent: {name}"
        setattr(agent, 'is_active', True)
        return f"✅ Agent @{name} 已激活"
    
    def cmd_deactivate(args, msg):
        if not args:
            return "用法: /deactivate <AgentName>"
        name = args[0]
        agent = messager.agents.get(name)
        if not agent:
            return f"找不到 Agent: {name}"
        setattr(agent, 'is_active', False)
        return f"✅ Agent @{name} 已停用"
    
    # 注册命令
    messager.register_command("help", cmd_help, "显示帮助信息")
    messager.register_command("list", cmd_list, "列出所有 Agent")
    messager.register_command("status", cmd_status, "查看 Agent 状态")
    messager.register_command("activate", cmd_activate, "激活 Agent")
    messager.register_command("deactivate", cmd_deactivate, "停用 Agent")
