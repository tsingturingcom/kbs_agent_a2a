# KBS 命令行客户端 | KBS Command Line Client

这是一个专为KBS_Agent_A2A设计的命令行客户端，提供了友好的交互式界面，用于与实现A2A协议的智能体进行对话。本客户端特别优化了针对知识库查询的结果展示，支持引用来源显示和多种交互模式。

This is a command line client specially designed for KBS_Agent_A2A, providing a friendly interactive interface for conversations with agents implementing the A2A protocol. This client has particularly optimized the display of knowledge base query results, supporting reference source display and multiple interaction modes.

## 功能特点 | Features

- **美观界面** | **Beautiful Interface**
  - 美观的命令行界面，使用Rich库渲染
  - Beautiful command line interface rendered with Rich library
  - 语法高亮和格式化输出
  - Syntax highlighting and formatted output

- **知识溯源** | **Knowledge Tracing**
  - 直观展示返回的知识库参考来源
  - Intuitive display of knowledge base references
  - 清晰呈现多个参考资料及其相关度
  - Clear presentation of multiple references and their relevance

- **多种响应模式** | **Multiple Response Modes**
  - 支持流式(实时)和非流式响应模式
  - Support for streaming (real-time) and non-streaming response modes
  - 提供进度展示和取消功能
  - Provides progress display and cancellation functionality

- **会话持久化** | **Session Persistence**
  - 保存会话上下文，实现多轮对话
  - Save session context for multi-turn conversations
  - 支持命名和恢复会话
  - Support for naming and restoring sessions

- **强大格式支持** | **Powerful Format Support**
  - 支持Markdown渲染
  - Support for Markdown rendering
  - 表格和代码块特殊处理
  - Special handling for tables and code blocks
  - 智能调整排版适应终端窗口
  - Intelligent layout adjustment to fit terminal windows

## 系统架构 | System Architecture

KBS命令行客户端采用分层设计，主要组件包括：

```
┌───────────────────┐
│                   │
│   用户界面层      │  # 处理用户输入和输出显示
│   UI Layer        │  # Handles user input and output display
│                   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│                   │
│   客户端逻辑层    │  # 管理会话和请求逻辑
│   Client Logic    │  # Manages session and request logic
│                   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│                   │
│   A2A 协议层      │  # 实现A2A协议的客户端
│   A2A Protocol    │  # Implements A2A protocol client
│                   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│                   │
│   网络通信层      │  # 处理HTTP请求和SSE流
│   Network Layer   │  # Handles HTTP requests and SSE streams
│                   │
└───────────────────┘
```

## 文件结构 | File Structure

```
hosts/kbs_cli/
├── __init__.py             # 模块初始化文件
├── __main__.py             # 入口点脚本
└── README.md               # 说明文档
```

- **__main__.py**: 主要实现文件，包含命令行界面和客户端逻辑
- **__init__.py**: 模块初始化文件

## 安装 | Installation

### 依赖项 | Dependencies

客户端依赖以下Python库：

- **rich**: 用于美化命令行界面和文本渲染
- **asyncclick**: 提供异步命令行接口
- **httpx** & **httpx-sse**: 用于HTTP请求和Server-Sent Events
- **pydantic**: 用于数据验证和序列化

### 安装步骤 | Installation Steps

```bash
# 方法1: 从项目根目录安装 | Method 1: Install from project root
pip install -e .

# 方法2: 安装特定依赖 | Method 2: Install specific dependencies
pip install rich asyncclick httpx httpx-sse pydantic
```

## 使用指南 | Usage Guide

### 基本用法 | Basic Usage

```bash
# 最简单的启动方式，连接到默认服务器 | Simplest way to start, connecting to default server
python -m hosts.kbs_cli --ragflow http://localhost:10003
```

### 命令行选项 | Command Line Options

- `--ragflow URL`: 指定RagFlow服务器URL | Specify RagFlow server URL
- `--session ID`: 使用特定会话ID | Use specific session ID
- `--stream/--no-stream`: 启用/禁用流式模式 | Enable/disable streaming mode
- `--timeout SECONDS`: 设置请求超时时间(秒) | Set request timeout in seconds
- `--verbose`: 显示详细的调试信息 | Show detailed debug information

### 交互式命令 | Interactive Commands

在交互式界面中，您可以使用以下特殊命令：

- `:q` 或 `quit` 或 `exit`: 退出程序 | Exit the program
- `:clear`: 清除屏幕 | Clear the screen
- `:history`: 显示对话历史 | Show conversation history
- `:save FILENAME`: 保存对话历史到文件 | Save conversation history to file
- `:help`: 显示帮助信息 | Show help information

## 详细功能说明 | Detailed Feature Description

### 代理卡片信息展示 | Agent Card Information Display

客户端会在启动时获取并展示代理的信息卡片：

```
┌──────────────────────────────────────────────────┐
│            RagFlow代理信息                       │
│                                                  │
│ 名称: RagFlow知识库代理                          │
│ 描述: 基于知识库的问答系统                        │
│ URL: http://localhost:10003                      │
│ 版本: 1.0.0                                      │
└──────────────────────────────────────────────────┘
技能:
• 知识检索: 从企业知识库中检索相关信息并回答问题

会话ID: 481e3d48-7ed4-4caa-b06e-05891836ea4b

请输入问题 (:q 退出):
```

### 流式处理 | Streaming Processing

在流式模式下，客户端会逐字显示回答内容，提供更好的用户体验：

```python
async def process_streaming_events(self, events, rich_console):
    """处理流式事件并实时显示"""
    text_buffer = ""
    with rich_console.status("[bold green]生成回答中...") as status:
        async for event in events:
            # 处理TaskStatusUpdateEvent
            if hasattr(event, 'status'):
                if event.status.message:
                    for part in event.status.message.parts:
                        if part.type == "text":
                            # 逐字显示文本
                            new_text = part.text
                            text_buffer += new_text
                            print(new_text, end="", flush=True)
            
            # 处理TaskArtifactUpdateEvent
            elif hasattr(event, 'artifact'):
                for part in event.artifact.parts:
                    if part.type == "text":
                        new_text = part.text
                        text_buffer += new_text
                        print(new_text, end="", flush=True)
    
    # 处理完成后美化显示
    rich_console.print("\n")
    return text_buffer
```

### 知识来源展示 | Knowledge Source Display

对于RagFlow返回的知识库引用，客户端会以清晰的格式展示：

```
回答: 量子计算是一种利用量子力学原理进行计算的技术...

📚 参考来源:
1. 《量子计算导论》 (相关度: 高)
   "量子计算是一种利用量子力学原理如叠加和纠缠来处理信息的计算模型..."
   
2. 《量子算法与应用》 (相关度: 中)
   "与经典计算机相比，量子计算机在特定问题上可以实现指数级的速度提升..."
```

### 会话管理 | Session Management

客户端使用会话ID管理多轮对话的上下文：

```python
class SessionManager:
    """会话管理器类"""
    
    def __init__(self):
        self.sessions = {}
    
    def get_or_create_session(self, session_id=None):
        """获取或创建会话"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "created_at": datetime.now()
            }
        
        return session_id, self.sessions[session_id]
    
    def add_to_history(self, session_id, message):
        """添加消息到会话历史"""
        if session_id in self.sessions:
            self.sessions[session_id]["history"].append(message)
    
    def get_history(self, session_id):
        """获取会话历史"""
        return self.sessions.get(session_id, {}).get("history", [])
```

## 技术实现细节 | Technical Implementation Details

### A2A客户端使用 | A2A Client Usage

客户端基于common模块的A2AClient实现，主要使用以下方法：

```python
# 获取代理卡片
resolver = A2ACardResolver(base_url=url)
agent_card = resolver.get_agent_card()

# 创建客户端
client = A2AClient(agent_card=agent_card)

# 构建任务参数
task_params = TaskSendParams(
    id=f"task-{uuid.uuid4().hex}",
    sessionId=session_id,
    message=Message(
        role="user",
        parts=[TextPart(type="text", text=query)]
    )
)

# 发送流式请求
if streaming:
    events = await client.send_task_subscribe(task_params)
    # 处理流式事件...
else:
    # 发送同步请求
    task = await client.send_task(task_params)
    # 处理响应...
```

### Rich库使用 | Rich Library Usage

客户端使用Rich库提供丰富的文本渲染和终端UI：

```python
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

# 创建控制台
console = Console()

# 显示面板
console.print(Panel(
    f"[bold]RagFlow代理信息[/bold]\n\n"
    f"名称: {agent_card.name}\n"
    f"描述: {agent_card.description or '无'}\n"
    f"URL: {agent_card.url}\n"
    f"版本: {agent_card.version}",
    title="代理信息",
    expand=False
))

# 渲染Markdown
markdown = Markdown(text)
console.print(markdown)

# 创建表格
table = Table(title="参考来源")
table.add_column("来源", style="cyan")
table.add_column("内容片段", style="green")
table.add_column("相关度", style="yellow")
# 添加行...
console.print(table)
```

### 异步处理 | Asynchronous Processing

客户端使用Python的asyncio进行异步操作：

```python
import asyncio
import signal

# 设置信号处理
loop = asyncio.get_event_loop()
signal.signal(signal.SIGINT, lambda s, f: loop.stop())

# 定义异步主函数
async def main():
    # 初始化客户端
    # 启动交互式循环
    # ...

# 运行主函数
if __name__ == "__main__":
    asyncio.run(main())
```

## 使用场景 | Usage Scenarios

### 1. 开发测试 | Development Testing

开发人员可以使用命令行客户端快速测试RagFlow代理功能，而无需搭建Web界面。

```bash
# 开发环境测试 | Development environment testing
python -m hosts.kbs_cli --ragflow http://localhost:10003 --verbose
```

### 2. 系统集成 | System Integration

系统集成人员可以通过命令行客户端验证API连接和响应格式。

```bash
# 验证生产环境可用性 | Verify production environment availability
python -m hosts.kbs_cli --ragflow https://production-api.example.com --no-stream
```

### 3. 知识库质量评估 | Knowledge Base Quality Assessment

知识库管理员可以使用客户端快速评估知识库的质量和回答准确性。

```bash
# 使用固定会话ID进行测试记录 | Test recording using fixed session ID
python -m hosts.kbs_cli --session quality-test-001 --ragflow http://localhost:10003
```

### 4. 脚本自动化 | Script Automation

可以将客户端集成到自动化脚本中，实现批量测试或监控。

```bash
# 示例：通过管道输入问题 | Example: Input questions through a pipe
echo "什么是量子计算?" | python -m hosts.kbs_cli --no-stream --ragflow http://localhost:10003
```

## 常见问题与解决方案 | Common Issues and Solutions

### 连接问题 | Connection Issues

#### 无法连接到服务器 | Cannot connect to server

**问题** | **Problem**: 无法连接到RagFlow服务器，显示连接错误。
Cannot connect to RagFlow server, showing connection error.

**解决方案** | **Solution**:
- 检查服务器URL是否正确，包括协议和端口 | Check if server URL is correct, including protocol and port
- 确保服务器正在运行 | Ensure the server is running
- 检查网络连接 | Check network connection
- 尝试使用ping或curl测试服务器连接 | Try using ping or curl to test server connection

#### HTTP错误 | HTTP errors

**问题** | **Problem**: 收到HTTP错误码。
Received HTTP error code.

**解决方案** | **Solution**:
- 401/403: 检查认证设置 | Check authentication settings
- 404: 检查URL路径是否正确 | Check if URL path is correct
- 500: 检查服务器日志 | Check server logs
- 尝试增加--verbose参数查看详细错误 | Try adding --verbose parameter to see detailed errors

### 显示问题 | Display Issues

#### 文本格式异常 | Abnormal text format

**问题** | **Problem**: 命令行中的格式显示异常。
Format display is abnormal in command line.

**解决方案** | **Solution**:
- 确保终端支持ANSI颜色 | Ensure terminal supports ANSI colors
- 检查终端字体和编码设置 | Check terminal font and encoding settings
- 尝试使用--no-stream模式 | Try using --no-stream mode

#### Unicode字符显示问题 | Unicode character display issues

**问题** | **Problem**: 特殊字符或表情符号显示为方块或问号。
Special characters or emojis display as squares or question marks.

**解决方案** | **Solution**:
- 确保使用支持Unicode的字体 | Ensure using a font that supports Unicode
- 在Windows上，尝试使用Windows Terminal代替cmd | On Windows, try using Windows Terminal instead of cmd
- 设置终端的编码为UTF-8 | Set terminal encoding to UTF-8

### 性能问题 | Performance Issues

#### 响应缓慢 | Slow response

**问题** | **Problem**: 客户端响应缓慢。
Client responds slowly.

**解决方案** | **Solution**:
- 检查网络连接速度 | Check network connection speed
- 增加超时设置: `--timeout 180` | Increase timeout setting: `--timeout 180`
- 对于复杂查询，延迟是正常的 | For complex queries, delay is normal

#### 内存占用高 | High memory usage

**问题** | **Problem**: 长时间运行后内存占用增加。
Memory usage increases after running for a long time.

**解决方案** | **Solution**:
- 定期重启客户端 | Regularly restart the client
- 限制会话历史大小 | Limit session history size
- 使用`:clear`命令清理内存 | Use `:clear` command to clean memory

## 与其他工具的比较 | Comparison with Other Tools

### vs. 通用A2A客户端 | vs. Generic A2A Client

相比通用A2A CLI客户端，KBS专用客户端的优势：

1. **更友好的界面** | **More Friendly Interface**
   - 美化了代理卡片和回答内容的显示
   - 使用颜色和样式突出重要信息

2. **专业的知识引用处理** | **Professional Knowledge Reference Processing**
   - 特别处理了知识库引用信息，清晰展示来源
   - 支持显示多个引用来源及其相关度

3. **简化的命令参数** | **Simplified Command Parameters**
   - 简化了命令行参数，专注于常用功能
   - 优化了默认设置，减少配置需求

### vs. Web客户端 | vs. Web Client

相比Web客户端，命令行客户端的优势：

1. **轻量级** | **Lightweight**
   - 不需要浏览器，资源占用低
   - 启动速度快，响应迅速

2. **脚本友好** | **Script Friendly**
   - 可以轻松集成到自动化脚本中
   - 支持管道和重定向

3. **离线环境适用** | **Suitable for Offline Environments**
   - 不需要图形界面，适用于SSH连接和服务器环境
   - 在网络条件受限环境中更可靠

## 开发者指南 | Developer Guide

### 代码结构 | Code Structure

KBS CLI客户端的主要代码结构：

```python
# __main__.py
# 1. 导入模块
from common.client import A2AClient, A2ACardResolver
from common.types import TaskSendParams, Message, TextPart, TaskState
import asyncclick as click
from rich.console import Console
# ...

# 2. 会话管理类
class SessionManager:
    # 会话管理实现
    # ...

# 3. 客户端类
class KBSCliClient:
    def __init__(self, url, streaming=True, timeout=120, session_id=None, verbose=False):
        # 初始化
        # ...
    
    async def connect(self):
        # 连接到服务器
        # ...
    
    async def ask(self, query):
        # 发送问题并处理响应
        # ...
    
    def display_agent_info(self):
        # 显示代理信息
        # ...
    
    async def process_streaming_events(self, events):
        # 处理流式事件
        # ...
    
    def format_references(self, data):
        # 格式化参考资料
        # ...
    
    # 其他辅助方法
    # ...

# 4. 命令行界面
@click.command()
@click.option('--ragflow', help='RagFlow代理URL')
@click.option('--session', help='会话ID')
@click.option('--stream/--no-stream', default=True, help='是否使用流式响应')
@click.option('--timeout', default=120, help='请求超时(秒)')
@click.option('--verbose', is_flag=True, help='显示详细日志')
async def cli(ragflow, session, stream, timeout, verbose):
    # 命令行入口点
    # ...

# 5. 主程序
if __name__ == '__main__':
    cli(_anyio_backend="asyncio")
```

### 扩展指南 | Extension Guide

要扩展KBS CLI客户端，可以考虑以下方向：

1. **添加新命令** | **Add New Commands**
   - 在交互式命令处理中添加新的特殊命令
   - 例如：添加`:config`命令修改运行时配置

2. **增强显示功能** | **Enhance Display Features**
   - 添加更多Rich组件支持，如进度条和图表
   - 支持图片和多媒体内容的处理

3. **添加插件系统** | **Add Plugin System**
   - 实现插件架构，支持自定义扩展
   - 允许通过配置文件加载插件

4. **支持本地缓存** | **Support Local Caching**
   - 实现查询结果的本地缓存
   - 提供离线模式支持

## 贡献指南 | Contribution Guidelines

我们欢迎对KBS CLI的贡献，请遵循以下准则：

1. **编码规范** | **Coding Standards**
   - 遵循PEP 8风格指南
   - 使用类型注解提高代码可读性
   - 为所有功能添加文档字符串

2. **测试** | **Testing**
   - 为新功能添加单元测试
   - 确保所有测试通过再提交
   - 提供测试用例和预期结果

3. **文档** | **Documentation**
   - 更新README.md反映新功能
   - 提供清晰的使用示例
   - 保持中英文双语文档格式

4. **提交PR** | **Submit PR**
   - 清晰描述功能或修复的问题
   - 使用有意义的提交信息
   - 保持小型、单一功能的提交

## 许可证 | License

KBS CLI客户端采用Apache License 2.0许可证。详情请参见LICENSE文件。
KBS CLI client is licensed under the Apache License 2.0. For details, please refer to the LICENSE file. 