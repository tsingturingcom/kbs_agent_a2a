# A2A协议基础设施模块 | A2A Protocol Core Infrastructure

本模块包含了KBS_Agent_A2A项目的核心协议实现，提供了A2A（Agent2Agent）协议的基础设施组件。它定义了智能体之间通信所需的数据类型、服务器框架、客户端工具和通用工具类，是整个KBS_Agent_A2A项目的基础。

This module contains the core protocol implementation for the KBS_Agent_A2A project, providing the infrastructure components for the A2A (Agent2Agent) protocol. It defines data types, server framework, client tools, and utility classes required for communication between intelligent agents, serving as the foundation for the entire KBS_Agent_A2A project.

## 模块结构 | Module Structure

```
common/
├── __init__.py                  # 模块初始化文件
├── types.py                     # 核心数据类型定义(365行)
├── server/                      # 服务器端实现
│   ├── __init__.py              # 服务器模块初始化
│   ├── server.py                # A2A服务器实现(121行)
│   ├── task_manager.py          # 任务管理器实现(278行)
│   └── utils.py                 # 服务器工具函数(29行)
├── client/                      # 客户端实现
│   ├── __init__.py              # 客户端模块初始化
│   ├── client.py                # A2A客户端实现(87行)
│   └── card_resolver.py         # 代理卡片解析器(22行)
└── utils/                       # 通用工具类
    ├── __init__.py              # 工具模块初始化
    ├── push_notification_auth.py # 推送通知认证(136行)
    └── in_memory_cache.py       # 内存缓存实现(110行)
```

## 核心功能详解 | Core Features

### 1. 数据类型定义 (types.py)

`types.py`是整个协议的基础，定义了所有A2A协议中使用的数据结构，确保客户端和服务器之间的通信标准化。

#### 1.1 核心数据类型

- **TaskState枚举**：定义任务所有可能的状态
  ```python
  class TaskState(str, Enum):
      SUBMITTED = "submitted"  # 已提交但尚未开始处理
      WORKING = "working"      # 正在处理中
      INPUT_REQUIRED = "input-required"  # 需要用户额外输入
      COMPLETED = "completed"  # 任务成功完成
      CANCELED = "canceled"    # 任务被取消
      FAILED = "failed"        # 任务失败
      UNKNOWN = "unknown"      # 未知状态(通常用于错误处理)
  ```

- **Part系统**：多模态内容的基本单元，支持三种类型
  ```python
  # 文本内容
  class TextPart(BaseModel):
      type: Literal["text"] = "text"
      text: str
      metadata: dict[str, Any] | None = None
      
  # 文件内容
  class FilePart(BaseModel):
      type: Literal["file"] = "file"
      file: FileContent  # 包含文件数据或URI
      metadata: dict[str, Any] | None = None
      
  # 结构化数据
  class DataPart(BaseModel):
      type: Literal["data"] = "data"
      data: dict[str, Any]  # 任意JSON结构化数据
      metadata: dict[str, Any] | None = None
  ```

- **消息和任务结构**
  ```python
  # 消息：用户或代理的一轮通信
  class Message(BaseModel):
      role: Literal["user", "agent"]  # 消息发送者角色
      parts: List[Part]               # 消息内容部分
      metadata: dict[str, Any] | None = None
      
  # 任务：工作单元
  class Task(BaseModel):
      id: str                        # 任务唯一标识符
      sessionId: str | None = None   # 会话ID，关联多个任务
      status: TaskStatus             # 当前任务状态
      artifacts: List[Artifact] | None = None  # 任务产出物
      history: List[Message] | None = None     # 消息历史
      metadata: dict[str, Any] | None = None   # 元数据
  ```

#### 1.2 代理发现元数据

- **AgentCard**：描述代理能力和元数据的关键结构
  ```python
  class AgentCard(BaseModel):
      name: str                     # 代理名称
      description: str | None = None # 描述
      url: str                      # 代理API端点URL
      provider: AgentProvider | None = None  # 提供者信息
      version: str                  # 版本号
      documentationUrl: str | None = None   # 文档URL
      capabilities: AgentCapabilities  # 支持的功能特性
      authentication: AgentAuthentication | None = None  # 认证方式
      defaultInputModes: List[str] = ["text"]  # 默认输入模式
      defaultOutputModes: List[str] = ["text"] # 默认输出模式
      skills: List[AgentSkill]      # 代理技能列表
  ```

#### 1.3 JSON-RPC消息

- 基于JSON-RPC 2.0标准的请求和响应结构
  ```python
  class JSONRPCRequest(JSONRPCMessage):
      method: str                   # 方法名
      params: dict[str, Any] | None = None  # 参数
      
  class JSONRPCResponse(JSONRPCMessage):
      result: Any | None = None     # 结果
      error: JSONRPCError | None = None  # 错误信息
  ```

- 支持的方法：
  - `tasks/send` - 发送任务请求
  - `tasks/sendSubscribe` - 发送任务并建立流式事件订阅
  - `tasks/get` - 获取任务状态和结果
  - `tasks/cancel` - 取消正在进行的任务
  - `tasks/pushNotification/set` - 配置推送通知
  - `tasks/pushNotification/get` - 获取推送通知配置
  - `tasks/resubscribe` - 重新订阅之前的任务流

#### 1.4 错误处理

- 标准化错误代码和消息格式
  ```python
  # JSON-RPC标准错误
  class JSONParseError(JSONRPCError):
      code: int = -32700
      message: str = "Invalid JSON payload"
      
  # A2A特定错误
  class TaskNotFoundError(JSONRPCError):
      code: int = -32001
      message: str = "Task not found"
  ```

### 2. 服务器实现 (server/)

#### 2.1 A2AServer (server.py)

`server.py`实现了基于Starlette的HTTP服务器，处理A2A协议的请求和响应。

- **核心功能**:
  - 初始化和启动HTTP服务器
  - 提供代理卡片端点(/.well-known/agent.json)
  - 解析JSON-RPC请求并路由到任务管理器
  - 支持同步响应和异步事件流(SSE)
  - 错误处理和异常管理

- **主要组件**:
  ```python
  class A2AServer:
      def __init__(
          self,
          agent_card: AgentCard,
          task_manager: TaskManager,
          host: str = "localhost",
          port: int = 8000,
      ):
          # 初始化服务器组件
      
      async def handle_agent_card(self, request):
          # 处理代理卡片请求
          
      async def handle_json_rpc(self, request):
          # 处理JSON-RPC请求
          
      def start(self):
          # 启动服务器
  ```

#### 2.2 任务管理器 (task_manager.py)

`task_manager.py`定义了任务管理的抽象接口和内存实现，是服务器的核心组件。

- **TaskManager抽象基类**:
  ```python
  class TaskManager(Protocol):
      # 任务管理的接口定义
      async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse: ...
      async def on_send_task_subscribe(self, request: SendTaskStreamingRequest) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse: ...
      async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse: ...
      async def on_cancel_task(self, request: CancelTaskRequest) -> CancelTaskResponse: ...
      async def on_set_push_notification(self, request: SetTaskPushNotificationRequest) -> SetTaskPushNotificationResponse: ...
      async def on_get_push_notification(self, request: GetTaskPushNotificationRequest) -> GetTaskPushNotificationResponse: ...
      async def on_resubscribe_to_task(self, request: TaskResubscriptionRequest) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse: ...
  ```

- **InMemoryTaskManager实现**:
  - 基于内存存储任务和状态
  - 提供完整的任务生命周期管理
  - 实现Server-Sent Events(SSE)用于实时更新
  - 管理推送通知配置和发送
  - 使用异步锁确保线程安全
  
  ```python
  class InMemoryTaskManager(TaskManager):
      def __init__(self):
          self.tasks: dict[str, Task] = {}  # 任务存储
          self.push_notification_infos: dict[str, PushNotificationConfig] = {}  # 推送通知配置
          self.lock = asyncio.Lock()        # 数据锁
          self.task_sse_subscribers: dict[str, List[asyncio.Queue]] = {}  # SSE订阅队列
          self.subscriber_lock = asyncio.Lock()  # 订阅者锁
      
      async def update_store(self, task_id: str, status: TaskStatus, artifacts: list[Artifact] | None) -> Task:
          # 更新任务状态和构件
          
      async def upsert_task(self, task_send_params: TaskSendParams) -> Task:
          # 创建或更新任务
          
      async def setup_sse_consumer(self, task_id: str, returnExisting: bool = False) -> asyncio.Queue:
          # 设置SSE事件队列
          
      async def enqueue_events_for_sse(self, task_id: str, event: TaskStatusUpdateEvent | TaskArtifactUpdateEvent | JSONRPCError):
          # 向所有订阅者队列发送事件
  ```

#### 2.3 服务器工具函数 (utils.py)

提供服务器端通用工具函数，如内容类型兼容性检查和错误响应生成。

```python
def are_modalities_compatible(
    client_accepted_modes: Optional[List[str]], server_supported_modes: List[str]
) -> bool:
    # 检查客户端和服务器内容类型兼容性
    
def new_incompatible_types_error(id: str | int | None) -> JSONRPCResponse:
    # 创建类型不兼容错误响应
    
def new_not_implemented_error(id: str | int | None) -> JSONRPCResponse:
    # 创建未实现操作错误响应
```

### 3. 客户端实现 (client/)

#### 3.1 A2A客户端 (client.py)

`client.py`实现了与A2A服务器通信的客户端库。

- **核心功能**:
  - 发送任务请求并接收响应
  - 处理流式和同步通信模式
  - 支持所有A2A协议方法
  - 错误处理和异常管理

- **主要组件**:
  ```python
  class A2AClient:
      def __init__(self, agent_card: AgentCard = None, url: str = None):
          # 客户端初始化
          
      async def send_task(self, task_send_params: TaskSendParams) -> Task:
          # 发送任务请求
          
      async def send_task_subscribe(self, task_send_params: TaskSendParams) -> AsyncIterable[TaskStatusUpdateEvent | TaskArtifactUpdateEvent]:
          # 发送任务并订阅事件流
          
      async def get_task(self, task_id: str, historyLength: int = None) -> Task:
          # 获取任务状态和结果
  ```

#### 3.2 代理卡片解析器 (card_resolver.py)

`card_resolver.py`实现了从服务器获取代理卡片的功能。

```python
class A2ACardResolver:
    def __init__(self, base_url: str, agent_card_path: str = ".well-known/agent.json"):
        # 初始化卡片解析器
        
    def get_agent_card(self) -> AgentCard:
        # 获取代理卡片并解析
```

### 4. 通用工具类 (utils/)

#### 4.1 推送通知认证 (push_notification_auth.py)

`push_notification_auth.py`实现了推送通知的安全认证机制。

- **PushNotificationSenderAuth**：服务器端推送通知认证
  ```python
  class PushNotificationSenderAuth(PushNotificationAuth):
      def __init__(self):
          super().__init__()
          self.jwk = None
          
      def generate_jwk(self):
          # 生成RSA密钥对
          
      async def verify_push_notification_url(self, url: str) -> bool:
          # 验证推送通知URL所有权
          
      async def send_push_notification(self, url: str, data: Any) -> bool:
          # 发送签名的推送通知
  ```

- **PushNotificationReceiverAuth**：客户端接收推送通知认证
  ```python
  class PushNotificationReceiverAuth(PushNotificationAuth):
      def __init__(self, token: str = None):
          super().__init__()
          self.token = token
          
      def verify_token(self, token: str) -> bool:
          # 验证令牌
          
      def verify_jwt(self, token: str, public_jwk_url: str) -> bool:
          # 验证JWT签名
  ```

#### 4.2 内存缓存 (in_memory_cache.py)

`in_memory_cache.py`实现了线程安全的内存缓存，用于缓存会话数据和临时信息。

```python
class InMemoryCache:
    _instance = None  # 单例模式
    
    def __init__(self):
        self.cache = {}  # 缓存存储
        self.lock = threading.Lock()  # 线程锁
        
    @classmethod
    def get_instance(cls):
        # 获取单例实例
        
    def set(self, key: str, value: Any, ttl: int = None):
        # 设置缓存值，可选TTL
        
    def get(self, key: str) -> Any:
        # 获取缓存值
        
    def delete(self, key: str) -> bool:
        # 删除缓存项
```

## 设计特点 | Design Features

### 1. 分离关注点

- **类型与实现分离**：核心数据类型与具体实现代码分离
- **接口与实现分离**：通过抽象基类定义接口，具体类实现功能
- **客户端与服务器分离**：明确的职责边界分工
- **功能模块化**：每个模块专注于单一职责

### 2. 类型安全和数据验证

- **Pydantic模型**：所有数据结构使用Pydantic模型确保类型安全
- **数据验证器**：内置验证逻辑确保数据一致性
- **枚举类型**：使用枚举表示固定选项，增强代码可读性

### 3. 异步编程和线程安全

- **asyncio异步框架**：全面使用Python异步编程模型
- **锁机制**：使用异步锁确保共享资源安全
- **异步迭代器**：支持流式数据处理

### 4. 可扩展性设计

- **插件化架构**：任务管理器可以被特定实现替换
- **协议接口稳定**：核心类型和接口保持稳定，便于扩展
- **中间件支持**：服务器架构支持添加中间件扩展功能

## 使用示例 | Usage Examples

### 创建A2A服务器

```python
from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill
from common.utils.push_notification_auth import PushNotificationSenderAuth
from your_agent_impl import YourTaskManager

# 创建代理卡片
agent_card = AgentCard(
    name="示例代理",
    description="示例A2A协议代理",
    url="http://localhost:8000/",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True, pushNotifications=True),
    skills=[
        AgentSkill(
            id="example_skill",
            name="示例技能",
            description="这是一个示例技能",
            examples=["示例查询"],
            inputModes=["text"],
            outputModes=["text"]
        )
    ],
)

# 创建推送通知认证
notification_sender_auth = PushNotificationSenderAuth()
notification_sender_auth.generate_jwk()

# 创建任务管理器和服务器
task_manager = YourTaskManager(agent=your_agent, notification_sender_auth=notification_sender_auth)
server = A2AServer(
    agent_card=agent_card,
    task_manager=task_manager,
    host="localhost",
    port=8000,
)

# 添加JWT密钥端点
server.app.add_route(
    "/.well-known/jwks.json", 
    notification_sender_auth.handle_jwks_endpoint, 
    methods=["GET"]
)

# 启动服务器
server.start()
```

### 使用A2A客户端

```python
import asyncio
from common.client import A2AClient
from common.types import TaskSendParams, Message, TextPart

async def main():
    # 创建客户端
    client = A2AClient(url="http://localhost:8000/")
    
    # 构建任务参数
    task_params = TaskSendParams(
        id="task-123",
        sessionId="session-456",
        message=Message(
            role="user",
            parts=[
                {
                    "type": "text",
                    "text": "示例查询"
                }
            ]
        )
    )
    
    # 发送任务
    task = await client.send_task(task_params)
    print(f"任务状态: {task.status.state}")
    
    # 检查结果
    if task.artifacts:
        for artifact in task.artifacts:
            for part in artifact.parts:
                if part.type == "text":
                    print(f"回答: {part.text}")

# 运行客户端
asyncio.run(main())
```

### 使用流式处理

```python
import asyncio
from common.client import A2AClient
from common.types import TaskSendParams, Message, TextPart, TaskState

async def main():
    client = A2AClient(url="http://localhost:8000/")
    
    # 构建任务参数
    task_params = TaskSendParams(
        id="task-123",
        sessionId="session-456",
        message=Message(
            role="user",
            parts=[
                {
                    "type": "text",
                    "text": "示例流式查询"
                }
            ]
        )
    )
    
    # 流式处理
    async for event in client.send_task_subscribe(task_params):
        if hasattr(event, 'status'):  # TaskStatusUpdateEvent
            print(f"状态更新: {event.status.state}")
            
            # 处理消息
            if event.status.message:
                for part in event.status.message.parts:
                    if part.type == "text":
                        print(f"中间消息: {part.text}")
            
            # 检查是否完成
            if event.final:
                print("任务完成")
                
        elif hasattr(event, 'artifact'):  # TaskArtifactUpdateEvent
            print(f"收到构件: {event.artifact.name}")
            
            # 处理构件内容
            for part in event.artifact.parts:
                if part.type == "text":
                    print(f"内容: {part.text}")

# 运行客户端
asyncio.run(main())
```

## 技术细节 | Technical Details

### 数据流程

1. **客户端发起请求**:
   - 创建任务参数(TaskSendParams)
   - 使用A2AClient发送JSON-RPC请求

2. **服务器处理请求**:
   - A2AServer接收请求并解析
   - 路由到TaskManager的相应方法
   - TaskManager处理任务并更新状态

3. **响应返回客户端**:
   - 对于同步请求，直接返回Task对象
   - 对于流式请求，通过SSE发送事件流
   - 对于推送通知，异步向注册的webhook URL发送更新

### 并发处理

- 使用`asyncio.Lock`保护共享资源访问
- 为每个任务维护独立的事件队列
- 使用异步迭代器实现非阻塞流处理

### 安全考虑

- JWT令牌用于推送通知认证
- 验证URL所有权确保安全通信
- 请求和响应验证防止恶意数据

## 与其他框架的整合 | Integration with Other Frameworks

common模块设计为框架无关的基础设施，可以轻松与各种AI框架整合:

1. **任务管理器适配**:
   - 创建特定框架的TaskManager子类
   - 实现方法将A2A协议转换为框架API调用

2. **会话状态映射**:
   - 使用sessionId关联框架的上下文或状态
   - 实现状态持久化和恢复

3. **内容转换**:
   - 定义框架特定输入/输出与A2A Part系统的映射
   - 处理多模态内容类型转换

## 高级使用技巧 | Advanced Usage Tips

### 1. 状态管理最佳实践

- 使用会话ID关联相关任务
- 在状态转换之间保持上下文连贯性
- 实现适当的错误恢复机制

### 2. 推送通知优化

- 针对长时间运行的任务使用推送通知
- 实现指数退避重试策略
- 处理推送失败的回退机制

### 3. 流式处理建议

- 启用流式处理提供实时反馈
- 发送有意义的中间状态更新
- 正确使用lastChunk标志表示流结束

### 4. 构件处理

- 对大型构件使用分块传输
- 正确设置MIME类型确保客户端正确处理
- 考虑使用URI引用而非内联字节数据