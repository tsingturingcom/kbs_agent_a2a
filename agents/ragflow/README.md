# RagFlow A2A Agent | RagFlow A2A 代理

该项目实现了RagFlow知识库系统的A2A协议适配，允许通过标准化的Agent2Agent协议与RagFlow交互，实现跨平台、跨系统的智能体互操作。
This project implements A2A protocol adapter for RagFlow knowledge base system, enabling interaction with RagFlow through the standardized Agent2Agent protocol, achieving cross-platform and cross-system agent interoperability.

## 功能特性 | Features

- **多模式支持** | **Multiple Modes Support**
  - 支持RagFlow聊天助手(Chat Assistant)和代理(Agent)两种模式
  - Supports both RagFlow Chat Assistant and Agent modes
  - 聊天助手模式适合简单问答，代理模式支持更复杂的交互
  - Chat Assistant mode is suitable for simple Q&A, Agent mode supports more complex interactions

- **实时交互** | **Real-time Interaction**
  - 流式响应支持，实时显示生成结果
  - Streaming response support for real-time result display
  - 逐字生成体验，减少等待感
  - Character-by-character generation experience, reducing waiting sensation

- **知识溯源** | **Knowledge Tracing**
  - 引用展示支持，展示回答来源和相关证据
  - Reference display support, showing answer sources and relevant evidence
  - 提高透明度和可信度
  - Enhances transparency and credibility

- **通知机制** | **Notification Mechanism**
  - 推送通知支持，实时接收任务状态更新
  - Push notification support for real-time task status updates
  - 支持长时间运行任务的状态监控
  - Supports status monitoring for long-running tasks

- **上下文管理** | **Context Management**
  - 会话管理和上下文保持，支持多轮对话
  - Session management and context preservation for multi-turn conversations
  - 会话状态持久化，确保对话连贯性
  - Session state persistence, ensuring conversation coherence

- **标准协议适配** | **Standard Protocol Adaptation**
  - 完整实现A2A协议规范，确保互操作性
  - Complete implementation of A2A protocol specification, ensuring interoperability
  - 支持所有A2A核心方法
  - Supports all A2A core methods

- **多数据库支持** | **Multiple Database Support**
  - 支持多种数据库存储任务和会话信息
  - Supports various database engines for storing tasks and session information
  - 包括SQLite、PostgreSQL、MySQL等
  - Including SQLite, PostgreSQL, MySQL, etc.
  - 通过配置文件灵活切换数据库类型
  - Flexibly switch database types through configuration file

## 系统架构 | System Architecture

RagFlow A2A Agent 采用了模块化设计，主要组件包括：
RagFlow A2A Agent adopts a modular design with the following main components:

```
┌─────────────────┐      ┌───────────────────┐      ┌──────────────────┐
│                 │      │                   │      │                  │
│   A2A 协议层    │◄────►│  RagFlow 适配层   │◄────►│  RagFlow API     │
│   A2A Protocol  │      │  RagFlow Adapter  │      │  RagFlow API     │
│                 │      │                   │      │                  │
└─────────────────┘      └───────────────────┘      └──────────────────┘
         ▲                        ▲
         │                        │
         ▼                        ▼
┌─────────────────┐      ┌───────────────────┐
│                 │      │                   │
│   任务管理器    │◄────►│  会话状态管理器   │
│  Task Manager   │      │  Session Manager  │
│                 │      │                   │
└─────────────────┘      └───────────────────┘
```

### 核心模块说明 | Core Module Description

- **A2A 协议层** | **A2A Protocol Layer**
  - 处理A2A协议请求和响应的格式转换
  - Handles format conversion of A2A protocol requests and responses
  - 基于common模块提供的类型定义和服务器框架
  - Based on type definitions and server framework provided by the common module
  - 实现所有必要的JSON-RPC方法
  - Implements all necessary JSON-RPC methods

- **RagFlow 适配层** | **RagFlow Adapter Layer**
  - 将A2A请求转换为RagFlow API调用
  - Converts A2A requests to RagFlow API calls
  - 封装RagFlow API客户端
  - Encapsulates RagFlow API client
  - 处理认证和异常情况
  - Handles authentication and exception cases

- **任务管理器** | **Task Manager**
  - 处理任务的创建、更新和状态管理
  - Handles creation, update, and status management of tasks
  - 继承InMemoryTaskManager实现
  - Inherits from InMemoryTaskManager implementation
  - 维护任务状态和生命周期
  - Maintains task state and lifecycle

- **会话状态管理器** | **Session State Manager**
  - 维护会话状态，实现上下文连续性
  - Maintains session state, implementing context continuity
  - 管理会话ID与RagFlow会话的映射
  - Manages mapping between session IDs and RagFlow sessions
  - 提供状态持久化能力
  - Provides state persistence capabilities

### 文件结构 | File Structure

```
agents/ragflow/
├── __init__.py                # 模块初始化文件
├── __main__.py                # 入口点，服务器启动代码
├── agent.py                   # RagFlow代理实现
├── task_manager.py            # 任务管理器实现
├── .env.example               # 环境变量示例文件
├── .env                       # 环境变量配置文件
└── README.md                  # 说明文档
```

- **__main__.py**: 服务器入口点，包含命令行解析和服务器初始化
- **agent.py**: RagFlow代理实现，包含与RagFlow API交互的核心逻辑
- **task_manager.py**: 特定于RagFlow的任务管理器实现，继承自common模块的InMemoryTaskManager

## 详细实现 | Detailed Implementation

### RagFlowAgent类 | RagFlowAgent Class

`agent.py`中的RagFlowAgent类是核心实现，负责与RagFlow API交互：

```python
class RagFlowAgent:
    def __init__(self, api_key, api_url, chat_id=None, agent_id=None):
        """初始化RagFlow代理"""
        self.api_key = api_key
        self.api_url = api_url
        self.chat_id = chat_id
        self.agent_id = agent_id
        # 验证配置有效性
        if not (chat_id or agent_id):
            raise ValueError("Either chat_id or agent_id must be provided")
        
        # 初始化API客户端
        self.setup_api_client()
    
    async def query(self, text, session_id=None):
        """向RagFlow发送查询"""
        # 构建请求体
        # 调用API
        # 处理响应
        
    async def stream_query(self, text, session_id=None):
        """向RagFlow发送流式查询"""
        # 构建请求体
        # 调用流式API
        # 处理流式响应
        # 返回生成器
```

### RagFlowTaskManager类 | RagFlowTaskManager Class

`task_manager.py`中的RagFlowTaskManager类继承自InMemoryTaskManager，处理任务管理：

```python
class RagFlowTaskManager(InMemoryTaskManager):
    def __init__(self, agent: RagFlowAgent, notification_sender_auth=None):
        """初始化RagFlow任务管理器"""
        super().__init__()
        self.agent = agent
        self.notification_sender_auth = notification_sender_auth
    
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """处理发送任务请求"""
        # 从请求中提取查询文本
        # 调用代理查询方法
        # 更新任务状态
        # 构建响应
        
    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """处理发送任务并订阅请求"""
        # 从请求中提取查询文本
        # 创建事件队列
        # 调用代理流式查询方法
        # 逐步更新任务状态
        # 返回生成器
```

## 前提条件 | Prerequisites

- Python 3.10+
- 访问RagFlow API的密钥 | RagFlow API key
- 已创建的RagFlow Chat Assistant或Agent | Created RagFlow Chat Assistant or Agent

## 安装 | Installation

### 1. 克隆代码库 | Clone the repository

```bash
git clone https://github.com/yourusername/kbs_agent_a2a.git
cd kbs_agent_a2a
```

### 2. 安装依赖 | Install dependencies

```bash
# 安装基础依赖 | Install base dependencies
pip install -e .

# 安装RagFlow专用依赖 | Install RagFlow specific dependencies
pip install -e ".[ragflow]"
```

## 配置 | Configuration

创建`.env`文件并配置以下环境变量:
Create a `.env` file and configure the following environment variables:

```bash
# RagFlow API密钥 | RagFlow API key
RAGFLOW_API_KEY=your-ragflow-api-key

# RagFlow API地址 | RagFlow API URL (默认为 | default: http://localhost:8000)
RAGFLOW_API_URL=http://your-ragflow-server:port

# 聊天助手ID | Chat assistant ID (使用聊天助手模式时需要 | required for chat assistant mode)
chat_assistants=your-chat-assistant-id

# 代理ID | Agent ID (使用代理模式时需要 | required for agent mode)
agent_id=your-agent-id

# 任务存储类型 | Task storage type (可选值: memory, database | possible values: memory, database)
TASK_STORAGE_TYPE=memory

# 任务数据库连接URL | Task database connection URL (当TASK_STORAGE_TYPE=database时需要 | required when TASK_STORAGE_TYPE=database)
TASK_DB_URL=sqlite+aiosqlite:///agents/ragflow/data/tasks.db

# 会话数据库连接URL | Session database connection URL
SESSION_DB_URL=sqlite:///agents/ragflow/data/sessions.db
```

您也可以参考`.env.example`文件作为模板。
You can also refer to the `.env.example` file as a template.

### 数据库配置 | Database Configuration

RagFlow代理支持两类独立的存储系统:
RagFlow agent supports two independent storage systems:

1. **任务存储** | **Task Storage**
   - 控制任务状态和结果的存储方式
   - Controls how task states and results are stored
   - 由`TASK_STORAGE_TYPE`环境变量控制
   - Controlled by the `TASK_STORAGE_TYPE` environment variable
   - 可选值: `memory`(内存存储), `database`(数据库存储)
   - Possible values: `memory` (in-memory storage), `database` (database storage)

2. **会话存储** | **Session Storage**
   - 管理会话状态和会话ID映射
   - Manages session states and session ID mappings
   - 始终使用数据库存储，不受`TASK_STORAGE_TYPE`影响
   - Always uses database storage, not affected by `TASK_STORAGE_TYPE`
   - 通过`SESSION_DB_URL`配置连接
   - Connection configured through `SESSION_DB_URL`

#### 支持的数据库类型 | Supported Database Types

##### SQLite (默认 | Default)
```
TASK_DB_URL=sqlite+aiosqlite:///agents/ragflow/data/tasks.db
SESSION_DB_URL=sqlite:///agents/ragflow/data/sessions.db
```

##### PostgreSQL
```
TASK_DB_URL=postgresql+asyncpg://username:password@localhost:5432/ragflow_tasks
SESSION_DB_URL=postgresql://username:password@localhost:5432/ragflow_sessions
```

##### MySQL
```
TASK_DB_URL=mysql+aiomysql://username:password@localhost:3306/ragflow_tasks
SESSION_DB_URL=mysql://username:password@localhost:3306/ragflow_sessions
```

#### 数据库安装与驱动 | Database Installation and Drivers

使用PostgreSQL或MySQL时，需要安装相应的Python数据库驱动:
When using PostgreSQL or MySQL, corresponding Python database drivers need to be installed:

```bash
# PostgreSQL驱动 | PostgreSQL drivers
pip install asyncpg psycopg2-binary

# MySQL驱动 | MySQL drivers
pip install aiomysql pymysql
```

#### 数据库自动创建 | Automatic Database Creation

系统会自动创建必要的数据库表和结构，无需手动创建。
The system automatically creates necessary database tables and structures, no manual creation required.

任务数据库结构:
Task database structure:
- 表: `tasks` - 存储任务状态和元数据
- Table: `tasks` - Stores task states and metadata

会话数据库结构:
Session database structure:
- 表: `session_mapping` - 存储A2A会话ID与RagFlow会话ID的映射
- Table: `session_mapping` - Stores mappings between A2A session IDs and RagFlow session IDs
- 表: `session_context` - 存储会话上下文和状态信息
- Table: `session_context` - Stores session contexts and state information

## 使用方法 | Usage

### 启动聊天助手模式 | Start chat assistant mode

```bash
python -m agents.ragflow --chat-id your-chat-id [--host localhost] [--port 10003] [--ragflow-url http://your-ragflow-server:port]
```

### 启动代理模式 | Start agent mode

```bash
python -m agents.ragflow --agent-id your-agent-id [--host localhost] [--port 10003] [--ragflow-url http://your-ragflow-server:port]
```

### 使用环境变量启动 | Start using environment variables

```bash
# 如果已经在.env文件中配置了chat_assistants
# If chat_assistants is already configured in .env file
python -m agents.ragflow

# 或者使用代理ID | Or use agent ID
python -m agents.ragflow --agent-id your-agent-id
```

### 命令行选项 | Command line options

- `--chat-id`: RagFlow Chat Assistant ID（与agent-id二选一 | mutually exclusive with agent-id）
- `--agent-id`: RagFlow Agent ID（与chat-id二选一 | mutually exclusive with chat-id）
- `--host`: 服务器主机名，默认为localhost | Server hostname, default is localhost
- `--port`: 服务器端口，默认为10003 | Server port, default is 10003
- `--ragflow-url`: RagFlow API URL，覆盖环境变量设置 | Overrides environment variable settings

## 技术详情 | Technical Details

### A2A协议响应方式 | A2A Protocol Response Methods

A2A协议提供了三种不同的响应方式，以适应不同的应用场景和需求。当前RagFlow A2A实现已经完整支持所有这三种响应方式，代码位于`common/server`目录：

#### 1. 同步响应（Synchronous Response）- 已实现
- **实现位置**：`server.py`中的`_process_request`和`_create_response`方法，`task_manager.py`中的`on_send_task`等
- **传输机制**：标准HTTP请求/响应
- **格式**：JSON-RPC 2.0响应格式
- **特点**：
  - 客户端发送请求后等待完整响应
  - 适合快速完成的任务
  - 单次请求-响应模式

**已实现代码示例**：
```python
# server.py中的实现
def _create_response(self, result: Any) -> JSONResponse | EventSourceResponse:
    if isinstance(result, JSONRPCResponse):
        return JSONResponse(result.model_dump(exclude_none=True))
```

#### 2. 流式响应（Streaming Response）- 已实现
- **实现位置**：`server.py`中的EventSourceResponse处理，`task_manager.py`和`db_task_manager.py`中的`dequeue_events_for_sse`方法
- **传输机制**：Server-Sent Events (SSE)
- **格式**：事件流，每个事件是一个JSON对象
- **特点**：
  - 建立长连接，服务器持续推送事件
  - 支持实时状态更新和进度报告
  - 适合长时间运行的任务
  - 包含TaskStatusUpdateEvent和TaskArtifactUpdateEvent

**已实现代码示例**：
```python
# server.py中的实现
def _create_response(self, result: Any) -> JSONResponse | EventSourceResponse:
    if isinstance(result, AsyncIterable):
        async def event_generator(result) -> AsyncIterable[dict[str, str]]:
            async for item in result:
                yield {"data": item.model_dump_json(exclude_none=True)}
        return EventSourceResponse(event_generator(result))
```

#### 3. 推送通知（Push Notifications）- 已实现
- **实现位置**：`task_manager.py`和`db_task_manager.py`中的`send_task_notification`方法，以及`common/utils/push_notification_auth.py`
- **传输机制**：HTTP webhook调用
- **格式**：带JWT认证的HTTP POST请求
- **特点**：
  - 服务器主动向客户端指定URL发送通知
  - 无需客户端保持连接
  - 适合异步通知和后台任务
  - 支持第三方系统集成

**已实现代码示例**：
```python
# task_manager.py中的实现
async def send_task_notification(self, task: Task):
    if not await self.has_push_notification_info(task.id):
        return
    push_info = await self.get_push_notification_info(task.id)
    await self.notification_sender_auth.send_push_notification(
        push_info.url,
        data=task.model_dump(exclude_none=True)
    )
```

#### 响应方式对比 | Response Method Comparison

所有这三种响应方式都已在RagFlow A2A服务器中完整实现，并通过以下API端点暴露：

| 响应方式 | 对应API方法 | 实现文件 | 实现状态 |
|---------|------------|---------|--------|
| 同步响应 | `tasks/send`, `tasks/get` | server.py, task_manager.py | ✅ 完全实现 |
| 流式响应 | `tasks/sendSubscribe`, `tasks/resubscribe` | server.py, task_manager.py | ✅ 完全实现 |
| 推送通知 | `tasks/pushNotification/set` | task_manager.py, utils/push_notification_auth.py | ✅ 完全实现 |

服务器端根据客户端的请求方式自动选择合适的响应方式，确保信息高效传递的同时保持灵活性，同时维护了接口规范的一致性和A2A协议的完整实现。

### 与A2A协议的集成 | Integration with A2A Protocol

#### 数据转换 | Data Transformation

RagFlow响应会被映射到A2A协议的以下元素：
RagFlow responses are mapped to the following A2A protocol elements:

- **文本内容** | **Text Content**: RagFlow的文本回答 → A2A的文本部分 | RagFlow text answer → A2A text part
- **引用来源** | **Reference Sources**: RagFlow的引用/来源 → A2A的数据部分 | RagFlow references → A2A data part

```json
{
  "parts": [
    {
      "type": "text",
      "text": "RagFlow生成的回答内容..."
    },
    {
      "type": "data",
      "data": {
        "references": {
          "chunks": [
            {
              "content": "参考文本片段",
              "source": "来源文档标题",
              "url": "来源URL(如果有)"
            }
          ]
        }
      }
    }
  ]
}
```

#### 状态映射 | State Mapping

RagFlow状态和A2A任务状态的映射关系：
Mapping between RagFlow states and A2A task states:

- **生成中** | **Generating**: RagFlow生成中 → TaskState.WORKING
- **已完成** | **Completed**: RagFlow完成生成 → TaskState.COMPLETED
- **错误** | **Error**: RagFlow错误状态 → TaskState.FAILED 或 TaskState.INPUT_REQUIRED

### 会话管理 | Session Management

- A2A的sessionId映射到RagFlow会话ID
- 使用内存缓存存储会话映射关系
- 支持会话持久化

### 流式处理实现 | Streaming Implementation

流式处理通过以下步骤实现：

1. 接收用户请求并创建任务
2. 调用RagFlow的流式API
3. 逐步更新TaskState.WORKING和消息内容
4. 所有内容接收完毕后设置状态为TaskState.COMPLETED

### 错误处理 | Error Handling

系统实现了多层错误处理：

- RagFlow API错误：捕获并转换为A2A错误格式
- 网络错误：重试机制和友好错误消息
- 认证错误：详细的错误提示和恢复建议

## 实际案例 | Practical Examples

### 使用Python客户端 | Using Python Client

```python
from common.client import A2AClient, A2ACardResolver
from common.types import TaskSendParams, Message, TextPart
import asyncio

async def main():
    # 获取代理卡片 | Get agent card
    resolver = A2ACardResolver(base_url="http://localhost:10003")
    agent_card = resolver.get_agent_card()

    # 创建客户端 | Create client
    client = A2AClient(agent_card=agent_card)

    # 构建任务参数 | Build task parameters
    task_params = TaskSendParams(
        id="task-123",
        sessionId="session-456",
        message=Message(
            role="user",
            parts=[TextPart(type="text", text="告诉我有关量子计算的知识")]
        )
    )

    # 发送任务 | Send task
    task = await client.send_task(task_params)
    print(f"任务状态: {task.status.state}")

    # 获取响应内容 | Get response content
    if task.artifacts:
        for artifact in task.artifacts:
            for part in artifact.parts:
                if part.type == "text":
                    print(f"回答: {part.text}")

# 运行客户端 | Run client
asyncio.run(main())
```

### 使用流式处理 | Using Streaming

```python
async def stream_example():
    # 创建客户端 | Create client
    client = A2AClient(url="http://localhost:10003")
    
    # 构建任务参数 | Build task parameters
    task_params = TaskSendParams(
        id="stream-task-123",
        sessionId="session-456",
        message=Message(
            role="user", 
            parts=[TextPart(type="text", text="详细解释机器学习的工作原理")]
        )
    )
    
    # 流式处理 | Stream processing
    async for event in client.send_task_subscribe(task_params):
        if hasattr(event, 'status'):  # TaskStatusUpdateEvent
            if event.status.message:
                for part in event.status.message.parts:
                    if part.type == "text":
                        print(part.text, end="", flush=True)
            
            if event.final:
                print("\n--- 任务完成 | Task completed ---")
                
asyncio.run(stream_example())
```

## 部署指南 | Deployment Guide

### Docker部署 | Docker Deployment

1. 创建Dockerfile | Create Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY . .
RUN pip install -e .

# 设置环境变量 | Set environment variables
ENV HOST=0.0.0.0
ENV PORT=10003

EXPOSE 10003

CMD ["python", "-m", "agents.ragflow"]
```

2. 构建镜像 | Build image

```bash
docker build -t ragflow-a2a-agent .
```

3. 运行容器 | Run container

```bash
docker run -p 10003:10003 \
  -e RAGFLOW_API_KEY=your-api-key \
  -e RAGFLOW_API_URL=http://your-ragflow-server:port \
  -e chat_assistants=your-chat-id \
  ragflow-a2a-agent
```

### 使用Supervisor进行进程管理 | Process Management with Supervisor

1. 创建配置文件 | Create configuration file

```ini
[program:ragflow-a2a]
command=python -m agents.ragflow
directory=/path/to/your/project
user=yourusername
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ragflow-a2a.log
environment=RAGFLOW_API_KEY="your-api-key",RAGFLOW_API_URL="http://your-ragflow-server:port",chat_assistants="your-chat-id"
```

2. 加载配置 | Load configuration

```bash
supervisorctl reread
supervisorctl update
```

3. 管理服务 | Manage service

```bash
supervisorctl status ragflow-a2a
supervisorctl restart ragflow-a2a
```

## 性能优化 | Performance Optimization

- **连接池**: 使用连接池管理与RagFlow的连接
- **缓存机制**: 实现常见查询的缓存
- **优雅降级**: 在高负载情况下的优雅降级策略
- **异步处理**: 充分利用异步API提高并发性能

## 故障排除 | Troubleshooting

### 常见问题 | Common Issues

1. **配置问题** | **Configuration Issues**
   - 检查环境变量是否正确设置
   - 确认RagFlow API密钥有效
   - 验证聊天助手ID或代理ID是否可访问

2. **连接错误** | **Connection Errors**
   - 确保RagFlow服务可访问
   - 检查网络连接和防火墙设置
   - 验证URL格式是否正确

3. **认证失败** | **Authentication Failures**
   - 检查API密钥格式和有效性
   - 确认有足够的权限访问指定的助手或代理

4. **响应超时** | **Response Timeouts**
   - 调整超时设置适应复杂查询
   - 考虑使用流式处理减少等待感

5. **数据库连接问题** | **Database Connection Issues**
   - 确保数据库服务正在运行
   - 验证数据库连接URL格式是否正确
   - 检查数据库用户权限是否足够
   - 确认数据库驱动已正确安装
   - SQLite数据库路径是否存在且可写

6. **数据库迁移** | **Database Migration**
   - 从内存存储切换到数据库存储时任务数据不会自动迁移
   - 从一种数据库类型切换到另一种时需要手动迁移数据

### 日志获取 | Getting Logs

服务器日志默认输出到控制台和log目录下的文件，可以通过以下方式获取：

```bash
# 查看日志文件 | View log files
cat log/ragflow_agent.log
cat log/kbs_a2a_server.log

# 使用Docker时查看日志 | View logs when using Docker
docker logs ragflow-a2a-container
```

### 数据库故障排查 | Database Troubleshooting

#### 检查数据库连接 | Check Database Connection

```bash
# SQLite
sqlite3 agents/ragflow/data/sessions.db ".tables"

# PostgreSQL
psql -h localhost -U username -d ragflow_sessions -c "\dt"

# MySQL
mysql -h localhost -u username -p -e "USE ragflow_sessions; SHOW TABLES;"
```

#### 数据库目录权限 | Database Directory Permissions

确保数据目录存在且有正确的权限:
Ensure the data directory exists and has correct permissions:

```bash
mkdir -p agents/ragflow/data
chmod 755 agents/ragflow/data
```

## 与其他系统的集成 | Integration with Other Systems

### 与其他A2A代理的集成 | Integration with Other A2A Agents

RagFlow A2A代理可以无缝地与其他支持A2A协议的代理进行通信：

```
┌─────────────┐     A2A     ┌───────────────┐
│ RagFlow A2A │◄──Protocol──►│ Other A2A     │
│ Agent       │             │ Agent         │
└─────────────┘             └───────────────┘
```

### 与Web应用的集成 | Integration with Web Applications

```
┌──────────┐     HTTP    ┌─────────────┐    A2A     ┌───────────┐
│ Web      │◄──Request──►│ Web Server  │◄─Protocol──►│ RagFlow   │
│ Browser  │             │ (Frontend)  │             │ A2A Agent │
└──────────┘             └─────────────┘             └───────────┘
```

## 贡献指南 | Contribution Guidelines

我们欢迎各种形式的贡献，包括但不限于：

- 功能改进和扩展
- 错误修复和问题报告
- 文档改进和翻译
- 测试用例补充

贡献步骤：

1. Fork项目并创建功能分支
2. 实现您的更改并添加测试
3. 确保所有测试通过
4. 提交拉取请求

## 许可证 | License

该项目采用 Apache License 2.0 许可证。有关详细信息，请参阅LICENSE文件。
This project is licensed under the Apache License 2.0. For details, see the LICENSE file. 