#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import pathlib

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))  # 只需上溯两级到项目根目录
sys.path.insert(0, project_root)  # 直接添加项目根目录

from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError, AgentProvider, AgentAuthentication
from common.utils.push_notification_auth import PushNotificationSenderAuth
from agents.ragflow.task_manager import RagFlowTaskManager
from agents.ragflow.agent import RagFlowAgent
from common.server.task_manager_factory import TaskManagerFactory
import click
import logging
from dotenv import load_dotenv
import asyncio

# 确保log目录存在
log_dir = pathlib.Path(project_root) / "log"
log_dir.mkdir(exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 控制台输出
        logging.FileHandler(log_dir / "ragflow_agent.log", encoding='utf-8')  # 文件输出
    ]
)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10003)
@click.option("--chat-id", "chat_id", default=None, help="RagFlow Chat ID, 与agent-id必须设置其中之一，如果未提供则从环境变量读取")
@click.option("--agent-id", "agent_id", default=None, help="RagFlow Agent ID, 与chat-id必须设置其中之一")
@click.option("--ragflow-url", "ragflow_url", default=None, help="RagFlow服务器URL，默认从环境变量RAGFLOW_API_URL或RAGFLOW_ENDPOINT读取")
@click.option("--storage-type", "storage_type", default=None, help="任务存储类型: memory或database，默认从环境变量TASK_STORAGE_TYPE读取")
@click.option("--db-url", "db_url", default=None, help="数据库连接URL，默认从环境变量TASK_DB_URL读取")
@click.option("--public-url", "public_url", default=None, help="公开访问的URL（如https://ragflow.example.com），用于AgentCard，与Nginx等反向代理配合使用")
def main(host, port, chat_id, agent_id, ragflow_url, storage_type, db_url, public_url):
    """启动RagFlow代理服务器"""
    
    # 设置环境变量
    if storage_type:
        os.environ['TASK_STORAGE_TYPE'] = storage_type
    else:
        # 默认使用数据库存储
        os.environ['TASK_STORAGE_TYPE'] = 'database'
        
    if db_url:
        os.environ['TASK_DB_URL'] = db_url
    else:
        # 默认使用agents/ragflow/data目录下的SQLite数据库
        os.environ['TASK_DB_URL'] = 'sqlite+aiosqlite:///agents/ragflow/data/tasks.db'
        
    # 加载环境变量
    load_dotenv()

    # 检查和设置RAGFLOW相关变量
    # ...现有代码保持不变...

    try:
        # 启动异步服务器
        asyncio.run(async_main(host, port, chat_id, agent_id, ragflow_url, public_url))
    except KeyboardInterrupt:
        logger.info("服务器已被用户中断")
    except Exception as e:
        logger.error(f"服务器启动错误: {e}", exc_info=True)

async def async_main(host, port, chat_id, agent_id, ragflow_url, public_url=None):
    """异步服务器启动实现"""
    # 验证API密钥和URL
    api_key = os.environ.get("RAGFLOW_API_KEY")
    if not api_key:
        raise MissingAPIKeyError("未设置RAGFLOW_API_KEY环境变量")
    
    # 如果命令行提供了URL，则覆盖环境变量
    if ragflow_url:
        os.environ["RAGFLOW_API_URL"] = ragflow_url
    
    # 如果未提供chat_id或agent_id，尝试从环境变量中获取
    if not chat_id and not agent_id:
        chat_assistants = os.environ.get("chat_assistants")
        if chat_assistants:
            # 如果有多个ID用逗号分隔，取第一个
            chat_id = chat_assistants.split(",")[0].strip()
            logger.info(f"从环境变量获取chat_id: {chat_id}")
    
    # 确认提供了chat_id或agent_id之一
    if not chat_id and not agent_id:
        logger.error("必须提供chat_id或agent_id之一")
        exit(1)
    
    # 根据传入的ID类型确定名称和描述
    if chat_id:
        agent_name = "RAG知识助手"
        agent_description = "基于RagFlow的知识库检索系统，提供问答服务"
        logger.info(f"使用聊天助手模式，ID: {chat_id}")
    else:
        agent_name = "RAG流程助手" 
        agent_description = "基于RagFlow的智能流程助手，可执行多步骤任务"
        logger.info(f"使用代理模式，ID: {agent_id}")
    
    # 获取RagFlow服务器URL
    ragflow_api_url = os.environ.get("RAGFLOW_API_URL") or os.environ.get("RAGFLOW_ENDPOINT")
    if ragflow_api_url:
        logger.info(f"使用RagFlow服务器: {ragflow_api_url}")

    # 确定代理能力
    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
    
    # 确定代理URL，优先使用public_url
    agent_url = public_url if public_url else f"http://{host}:{port}/"
    
    # 创建代理卡片
    agent_card = AgentCard(
        name=agent_name,
        description=agent_description,
        url=agent_url,  # 使用动态确定的URL
        version="1.0.0",
        defaultInputModes=RagFlowAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=RagFlowAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        provider=AgentProvider(
            organization="tsingturing",
            url="https://www.tsingturing.com"
        ),
        documentationUrl="https://www.tsingturing.com",
        skills=[
            AgentSkill(
                id="retrieve_knowledge",
                name="知识检索",
                description="从知识库中检索信息并提供答案",
                tags=["知识库", "RAG", "检索增强生成"],
                examples=["关于这个项目有什么文档?", "谁是该项目的负责人?", "项目的技术架构是什么?"],
                inputModes=["text"],
                outputModes=["text"]
            )
        ],
        # A2A协议标准可选字段：身份验证设置 | A2A Protocol optional standard field: authentication settings
        # 注意：虽然这里定义了认证结构，但当前服务端实际上并未启用认证验证
        # Note: Although authentication structure is defined here, the server does not actually enforce authentication currently
        # 这种配置会让客户端知道服务支持哪些认证方式，但不会强制客户端提供认证信息
        # This configuration informs clients about supported authentication methods without requiring them to authenticate
        # 未来计划启用认证时，可直接修改服务端代码而无需更改此定义
        # When authentication is to be enabled in the future, server code can be modified without changing this definition
        #
        # A2A协议支持的认证方式包括：| Authentication methods supported by A2A protocol include:
        # 1. apiKey: API密钥认证，通常在HTTP头或查询参数中传递简单的令牌 | API key authentication, typically a simple token passed in HTTP headers or query parameters
        # 2. oauth2: OAuth 2.0授权框架，支持多种授权流程，适用于用户授权场景 | OAuth 2.0 authorization framework, supports various flows, suitable for user authorization scenarios
        # 3. jwt: JSON Web Token认证，用于安全传输声明，适合跨服务认证 | JSON Web Token authentication, for secure claims transfer, ideal for cross-service authentication
        # 4. basic: 基本HTTP认证，使用用户名和密码 | Basic HTTP authentication using username and password
        # 5. openid: OpenID Connect身份认证，基于OAuth 2.0扩展，提供身份层 | OpenID Connect authentication, extends OAuth 2.0 with an identity layer
        authentication=AgentAuthentication(
            schemes=["apiKey", "oauth2"],  # 支持的认证方案 | Supported authentication schemes
            credentials=None,  # 默认凭证 | Default credentials
            securityDefinitions={  # 安全定义 | Security definitions
                "apiKey": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-KEY",
                    "description": "用于API认证的密钥 | API key for authentication"
                },
                "oauth2": {
                    "type": "oauth2",
                    "flows": {
                        "clientCredentials": {
                            "tokenUrl": "https://auth.tsingturing.com/token",
                            "scopes": {
                                "ragflow:read": "读取知识库内容 | Read knowledge base content",
                                "ragflow:query": "查询知识库 | Query knowledge base"
                            }
                        }
                    }
                }
            }
        ),
        
        # A2A协议标准可选字段：性能指标 | A2A Protocol optional standard field: performance metrics
        metrics={
            "averageResponseTime": "暂未测量",  # 平均响应时间 | Average response time
            "successRate": "暂未统计"  # 成功率 | Success rate
        },
        
        # A2A协议标准可选字段：使用限制 | A2A Protocol optional standard field: usage limits
        limits={
            "requestsPerMinute": None,  # 每分钟请求数限制 | Request rate limit per minute
            "maxMessageLength": None    # 最大消息长度限制 | Maximum message length limit
        },
        
        # A2A协议标准可选字段：定价信息 | A2A Protocol optional standard field: pricing information
        pricing={
            "model": "free",  # 定价模式：免费 | Pricing model: free
            "details": "免费服务"  # 定价详情 | Pricing details
        },
        
        # 自定义元数据，用于非标准扩展字段 | Custom metadata for non-standard extension fields
        metadata={
            "customField": "示例值",  # 自定义字段示例 | Example of custom field
            "environment": "development",  # 环境标识 | Environment identifier
            "implementationNotes": "RagFlow A2A适配器实现" # 实现说明 | Implementation notes
        }
    )
    
    # 创建RagFlow代理实例
    agent = RagFlowAgent(chat_id=chat_id, agent_id=agent_id)
    
    # 创建推送通知认证
    notification_sender_auth = PushNotificationSenderAuth()
    notification_sender_auth.generate_jwk()
    
    # 使用任务管理器工厂创建底层任务管理器（内存或数据库）
    logger.info("创建底层任务管理器...")
    base_task_manager = await TaskManagerFactory.create_task_manager()
    
    # 创建RagFlow任务管理器（使用组合模式）
    logger.info("创建RagFlow任务管理器...")
    ragflow_task_manager = RagFlowTaskManager(
        task_manager=base_task_manager,
        agent=agent, 
        notification_sender_auth=notification_sender_auth
    )
    
    # 创建服务器实例
    server = A2AServer(
        agent_card=agent_card,
        task_manager=ragflow_task_manager,
        host=host,
        port=port,
    )
    
    # 添加JWKS端点
    server.app.add_route(
        "/.well-known/jwks.json", 
        notification_sender_auth.handle_jwks_endpoint, 
        methods=["GET"]
    )
    
    # 启动服务器（使用异步方法）
    logger.info(f"启动服务器 {host}:{port}")
    await server.start_async()

if __name__ == "__main__":
    main() 