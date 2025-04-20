# KBS Agent A2A: 智能体协议适配中间件

**_基于谷歌开源A2A协议的多框架智能体互操作性适配层实现_**

## 项目定位

KBS_Agent_A2A 是一个**协议适配中间件**（Protocol Adaptation Middleware），专注于实现谷歌开源的 Agent2Agent (A2A) 协议标准。该项目旨在解决不同AI框架和厂商构建的智能体之间的互操作性问题，提供标准化的通信接口和数据交换格式。

- **KBS**：代表Knowledge-Based Sharing（基于知识的分享），体现项目开放分享的理念
- **Agent**：指智能体，负责执行特定任务的软件实体
- **A2A**：代表对Google Agent2Agent协议的实现与适配

## 项目仓库

- **GitHub仓库**: [https://github.com/tsingturingcom/kbs_agent_a2a](https://github.com/tsingturingcom/kbs_agent_a2a)

## 项目来源

本项目基于以下谷歌官方资源开发：

- **A2A协议官方文档**：[https://google.github.io/A2A/#/documentation](https://google.github.io/A2A/#/documentation)
  - 提供了协议的详细规范、核心概念和实现指南
  - 包含任务状态流转、消息格式和API接口定义

- **A2A参考实现**：[https://github.com/google/A2A](https://github.com/google/A2A)
  - 谷歌官方提供的示例代码和参考实现
  - 包含多种框架的样例和演示应用

我们的项目在这些基础上进行了扩展，实现了针对RagFlow和Dify等框架的协议适配。

## 框架适配

目前，本项目实现了以下框架的A2A协议适配：

### RagFlow适配
RagFlow是一个专注于**检索增强生成**（Retrieval-Augmented Generation, RAG）的框架，主要功能是将大型语言模型与外部知识库结合，提升生成内容的准确性和相关性。本项目通过**API规范化**和**协议封装**，使RagFlow能够与其他支持A2A协议的系统进行标准化通信。

### Dify适配（计划中）
Dify是一个开源的**LLMOps**（大语言模型运维）平台，提供可视化的AI应用构建工具和运行环境。我们计划进行**跨平台协议兼容**工作，使Dify能够通过A2A协议与其他智能体系统进行标准化交互。

## 技术架构

项目采用模块化设计，主要包含三个核心部分：

- **common**: 共享基础设施，实现**协议抽象层**（Protocol Abstraction Layer）
  - **client**: A2A客户端实现，用于与服务器通信
  - **server**: 服务器端基础组件，包括任务管理器
  - **utils**: 通用工具类，如推送通知认证、缓存等
  - **types.py**: 核心数据类型定义，实现A2A协议的数据结构

- **agents**: 智能体服务器实现，**适配器模式**（Adapter Pattern）应用
  - **ragflow**: 专为RAG流程设计的智能体适配器，实现协议转换和能力映射

- **hosts**: 客户端应用实现，作为**互操作性桥接器**（Interoperability Bridge）
  - **kbs_cli**: 命令行客户端，用于与适配后的智能体交互

## 核心功能

- **协议标准化实现**: 完整实现A2A协议规范，提供统一的API接口
- **适配器转换层**: 将特定框架API映射到A2A协议规范
- **多模态交互支持**: 支持文本、文件等多种内容类型的交互
- **实时状态同步**: 通过流式处理和推送通知机制实现实时状态更新
- **安全认证机制**: 支持JWT认证和请求签名验证
- **会话状态管理**: 维护多轮对话上下文和状态

## 快速开始

### 安装依赖

```bash
pip install -e .
```

### 使用启动脚本

我们提供了简便的启动脚本来运行服务器和客户端：

#### 启动服务器

```bash
# 使用默认设置启动服务器（localhost:10003）
python start_server.py

# 指定主机和端口
python start_server.py 192.168.1.100:8080

# 指定聊天ID和RagFlow API URL
python start_server.py localhost:10003 --chat-id=abc123 --url=https://api.example.com
```

#### 启动客户端

```bash
# 连接到默认服务器（localhost:10003）
python start_client.py

# 连接到指定服务器
python start_client.py http://192.168.1.100:8080
```

### 使用Python模块

您也可以直接使用Python模块启动：

#### 启动服务器

```bash
python -m agents.ragflow
```

#### 使用命令行客户端

```bash
python -m hosts.kbs_cli --ragflow http://localhost:10003
```

## A2A协议简介

A2A（Agent2Agent）是谷歌推出的开源协议，旨在解决企业AI采用过程中不同框架和厂商构建的智能体之间的互操作性问题。该协议提供了一种标准化的方式，使智能体能够：

- 相互发现和展示能力（能力发现机制）
- 协商交互方式和内容类型（模态协商）
- 安全协作完成复杂任务（任务协同）
- 支持实时状态更新和推送通知（状态同步）

### 协议核心组件

1. **JSON-RPC通信**: A2A基于JSON-RPC 2.0标准实现，支持HTTP(S)请求/响应和Server-Sent Events (SSE)流式通信
2. **AgentCard**: 智能体元数据描述文件（通常位于`/.well-known/agent.json`），包含名称、描述、URL、支持的输入/输出模式、技能列表等
3. **Task生命周期**: 任务状态流转模型，包括submitted、working、input-required、completed、canceled、failed等状态
4. **多模态内容**: 通过Part系统支持文本(TextPart)、文件(FilePart)和结构化数据(DataPart)
5. **标准化API方法**:
   - `tasks/send`: 发送任务请求
   - `tasks/sendSubscribe`: 发送任务并建立流式事件订阅
   - `tasks/get`: 获取任务状态和结果
   - `tasks/cancel`: 取消正在进行的任务
   - `tasks/pushNotification/set`: 配置推送通知
   - `tasks/pushNotification/get`: 获取推送通知配置
   - `tasks/resubscribe`: 重新订阅之前的任务流

### 高级功能特性

- **流式处理**: 长时间运行的任务可通过SSE提供实时更新，以`TaskStatusUpdateEvent`和`TaskArtifactUpdateEvent`形式发送
- **推送通知**: 支持通过webhook和JWT安全认证机制实现主动推送任务状态更新
- **构件流式传输**: 对于大型构件，支持分块传输，具有append和lastChunk标记
- **状态转换历史**: 可选支持详细的任务状态变化历史记录
- **错误处理机制**: 标准化的错误代码和消息格式，包括JSON-RPC标准错误和A2A特定错误

### A2A核心概念

- **AgentCard(智能体卡片)**: 公共元数据文件，描述智能体的能力、技能、端点URL和认证需求，供客户端用于发现
- **Task(任务)**: 工作的核心单元，具有唯一ID，通过状态流转(submitted→working→input-required→completed/failed/canceled)管理生命周期
- **Message(消息)**: 表示客户端(role:"user")和智能体(role:"agent")之间的通信轮次，包含Parts
- **Part(部分)**: Message或Artifact中的基本内容单元，可以是TextPart、FilePart(带内联字节或URI)或DataPart(结构化JSON数据)
- **Artifact(构件)**: 表示智能体在任务执行过程中生成的输出(如生成的文件、最终的结构化数据)，也包含Parts
- **TaskStatus(任务状态)**: 描述任务的当前状态，包含state(状态)、message(消息)和timestamp(时间戳)信息
- **Event(事件)**: 流式更新中的基本通信单元，包括TaskStatusUpdateEvent(状态更新)和TaskArtifactUpdateEvent(构件更新)
- **Session(会话)**: 上下文容器，可包含多个相关任务，维持对话连贯性，通过sessionId标识

### 会话、任务与消息的关系

A2A协议中，会话、任务和消息形成了多级嵌套的层次结构：

```
Session (会话)
└── Task (任务) - 可以有多个
    ├── Message (消息) - 可以有多个
    │   └── Part (部分) - 每个消息可以有多个部分
    └── Artifact (构件) - 可以有多个
        └── Part (部分) - 每个构件可以有多个部分
```

这种结构支持多种使用模式：

1. **一个任务一个消息**: 适用于独立问答场景，简单直接
2. **一个任务多个消息**: 适用于多步骤流程，如需要澄清的交互式对话
3. **一个会话多个任务**: 适用于复杂应用中的子任务划分，保持上下文连贯性

在实际应用中：
- 会话是状态和上下文的持有者，通过`sessionId`字段关联多个任务
- 任务是工作单元，有明确的状态和生命周期，包含用户与智能体的交互消息
- 消息是通信单元，表达用户需求或智能体响应，由多个内容部分组成
- 构件是任务的输出产物，可能随着任务进行而逐步生成或更新

A2A协议注重"会话(Session)"而非"用户(User)"，使系统能够在不要求显式用户注册的情况下，通过会话ID维护状态和上下文连贯性。

### 安全与认证

- **多种认证方案**: 在AgentCard中定义，支持API密钥、OAuth、JWT等
- **推送通知安全**: 使用挑战-响应模式进行URL验证，以及JWT令牌确保通信安全
- **请求签名验证**: 确保请求完整性和来源可信
- **授权模型**: 实现基于角色的访问控制，确保只有具有正确凭证和权限的智能体才能参与关键工作流
- **数据加密**: 要求在整个通信生命周期中进行加密数据交换，保护敏感信息

这些组件共同构成了一个完整、灵活且安全的智能体通信生态系统，为企业级AI应用提供了标准化的互操作性解决方案。

## 环境变量配置

服务器运行时需要设置以下环境变量：

| 环境变量 | 描述 | 必需 |
|-------------|-------------|---------|
| RAGFLOW_API_KEY | RagFlow API密钥，用于身份验证 | 是 |
| RAGFLOW_API_URL | RagFlow API基础URL | 是 |
| chat_assistants | 聊天助手ID（优先使用命令行参数） | 否 |

您可以在项目根目录或agents/ragflow目录下创建`.env`文件来设置这些变量：

```dotenv
RAGFLOW_API_KEY=your_api_key_here
RAGFLOW_API_URL=https://api.ragflow.ai
chat_assistants=chat_id1,chat_id2
```

## 技术价值

本项目代表了AI系统集成领域的重要工作：

- **标准化实现**: 将理论协议规范转化为可用的实际代码
- **生态系统扩展**: 扩展A2A协议生态，增加支持该协议的系统数量
- **框架互通**: 使不同框架(RagFlow和Dify)能够互相通信
- **开发者工具**: 为开发者提供标准化的接口和工具，简化多智能体系统的开发

## 贡献指南

欢迎贡献代码、报告问题或提出新功能建议。请阅读[贡献指南](CONTRIBUTING.md)了解详情。

联系我们：kbs@tsingturing.com

## 开源协议

本项目采用 [Apache License 2.0](LICENSE) 开源协议。

## 致谢

本项目基于以下资源开发，特此感谢：

- **Google A2A协议**：感谢谷歌团队开发并开源的[A2A协议文档](https://google.github.io/A2A/#/documentation)，为智能体互操作性提供了基础标准
- **Google A2A代码库**：感谢谷歌团队提供的[A2A参考实现](https://github.com/google/A2A)和示例代码，为本项目提供了技术指导
- **开源社区**：感谢各开源项目和贡献者提供的技术支持和灵感