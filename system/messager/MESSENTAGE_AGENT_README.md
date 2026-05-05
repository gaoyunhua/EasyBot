# Message Agent

Message Agent 是一个智能消息处理代理，支持 CLI 和 WeChat 平台，具备复杂的请求检测能力。

## 功能特性

### 1. 消息路由
- **CLI 平台**: 命令行界面
- **WeChat 平台**: 微信消息处理

### 2. 复杂请求检测
- 基于 LLM 的复杂请求检测
- 只在有 LLM provider 时激活
- 自动创建项目管理器代理

### 3. 项目管理器创建
- 使用 SystemAgentCaller → SystemBuilder → SystemTester 序列
- 根据请求类型创建不同的代理
- 支持桥牌 AI、数据分析等特定领域

### 4. 内存存储
- 使用 JSON 格式存储
- 位置：`/mnt/d/gyh/Projects/TRAE/EasyBot/memory.json`
- 存储消息历史和问题记录

## 安装依赖

确保已安装以下依赖：

```bash
python3 -m pip install -r requirements.txt
```

## 使用方法

### 基本使用

```python
from workspace.agent.message.message_agent.main import MessageAgent

# 初始化代理
agent = MessageAgent()

# 检查 LLM 是否可用
has_llm = agent.detect_llm_provider()

# 检测复杂请求
is_complex, req_type = agent.detect_complex_request("消息内容")

# 发送消息
agent.send_message("Hello", platform="wechat")

# 显示状态
agent.show_status()
```

### 完整示例

```python
from workspace.agent.message.message_agent.main import MessageAgent

# 创建代理实例
agent = MessageAgent()

# 演示消息处理
print("测试消息处理...")

# 简单消息
simple_msg = "你好"
is_complex, req_type = agent.detect_complex_request(simple_msg)
print(f"简单消息：复杂={is_complex}")

# 复杂消息（需要 LLM）
complex_msg = "创建一个桥牌 AI 训练器"
is_complex, req_type = agent.detect_complex_request(complex_msg)
print(f"复杂消息：复杂={is_complex}, 类型={req_type}")

if is_complex and has_llm:
    # 创建项目管理器
    success, agent_name = agent.create_project_manager_agent(req_type, complex_msg)
    print(f"创建代理：{agent_name}")

# 查看状态
agent.show_status()
```

## API 参考

### MessageAgent 类

#### `detect_llm_provider() -> bool`
检测是否有 LLM provider 可用。

```python
has_llm = agent.detect_llm_provider()  # True/False
```

#### `detect_complex_request(message: str) -> tuple`
检测消息是否为复杂请求。

- **参数**:
  - `message`: 消息内容

- **返回**:
  - `is_complex`: bool - 是否为复杂请求
  - `req_type`: str - 需要的代理类型

#### `create_project_manager_agent(req_type: str, message: str) -> tuple`
为复杂请求创建项目管理器代理。

- **参数**:
  - `req_type`: str - 代理类型
  - `message`: str - 原始请求

- **返回**:
  - `success`: bool - 是否创建成功
  - `agent_name`: str - 创建的代理名称

#### `send_message(message: str, platform: str) -> bool`
向指定平台发送消息。

- **参数**:
  - `message`: str - 消息内容
  - `platform`: str - 平台 ("cli" 或 "wechat")

- **返回**: bool - 发送是否成功

#### `show_status()`
显示代理状态和最近消息。

```python
agent.show_status()
```

#### `save_to_memory()`
保存消息到内存存储。

```python
agent.save_to_memory()
```

#### `load_from_memory()`
从内存存储加载消息。

```python
agent.load_from_memory()
```

## 平台配置

Message Agent 支持以下平台：

### CLI (命令行)
```python
agent.send_message("Hello from CLI", platform="cli")
```

### WeChat (微信)
```python
agent.send_message("Hello from WeChat", platform="wechat")
```

## 复杂请求类型

根据消息内容自动识别以下类型的复杂请求：

- **project_manager**: 通用项目管理
- **bridge_ai_trainer**: 桥牌 AI 训练
- **data_analyst**: 数据分析

### 识别关键词

```python
# 项目管理相关
- create, build, design, develop, implement
- agent, assistant, system, framework

# 桥牌 AI 相关
- bridge, bridgeai, endplay

# 数据分析相关
- data, analysis, quant, trading
```

## 内存存储

### 存储格式

```json
{
  "messages": [
    {
      "type": "complex",
      "content": "消息内容",
      "action": "创建代理名称"
    },
    {
      "type": "normal",
      "content": "普通消息"
    }
  ],
  "complex_questions": [...],
  "updated_at": "2024-01-01T12:00:00"
}
```

### 存储位置

```
/mnt/d/gyh/Projects/TRAE/EasyBot/memory.json
```

## 项目模板

Message Agent 使用以下模板创建代理：

```
/workspace/agent/project_manager/agent.md
```

## 测试

运行测试脚本：

```bash
# 运行完整测试
python3 test_message_agent.py

# 运行演示
python3 demo_message_agent.py
```

## 要求

- Python 3.10+
- EasyBot 系统
- Markdown Engine
- System Agent Builder/Caller/Tester

## 注意事项

1. **LLM 检测**: 复杂请求检测只在检测到 LLM provider 时才激活
2. **代理创建**: 需要 SystemBuilder 和 SystemTester 可用
3. **内存存储**: 复杂请求会保存在 memory.json 中
4. **模板依赖**: 需要 project_manager 模板文件存在

## 故障排除

### 导入错误
```
ImportError: cannot import name 'MessageAgent'
```

**解决**: 确保目录结构正确：
```
workspace/agent/message/
├── __init__.py
└── message_agent/
    ├── __init__.py
    └── main.py
```

### LLM 检测失败
```
No LLM provider detected
```

**解决**: 
- 检查环境变量（OPENAI_API_KEY, ANTHROPIC_API_KEY 等）
- 检查 system/config.yaml 中的 LLM 配置

### 代理创建失败
```
ModuleNotFoundError: No module named 'workspace.agent.project_manager'
```

**解决**: 确保模板文件存在：
```
/workspace/agent/project_manager/agent.md
```

## 更新日志

### 2024-04-22
- 初始版本
- 支持 CLI 和 WeChat 平台
- LLM 检测功能
- 复杂请求检测
- 项目管理器创建
- 内存存储

## 许可证

MIT License

---

**Author**: System  
**Version**: 1.0.0  
**Created**: 2024
