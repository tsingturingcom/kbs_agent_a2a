#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# 添加项目根目录到Python路径（如果尚未添加）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))  # 只需上溯两级到项目根目录
if project_root not in sys.path:
    sys.path.insert(0, project_root)  # 直接添加项目根目录

import httpx
import json
import logging
from typing import Dict, Any, AsyncIterable, Literal, Optional, List
from pydantic import BaseModel
import asyncio
import time
import random
from agents.ragflow.session_manager import SessionManager

logger = logging.getLogger(__name__)

# 全局配置
DEFAULT_TIMEOUT = 180.0  # 增加默认超时到3分钟
MAX_RETRIES = 3          # 最大重试次数
RETRY_BACKOFF = [1, 3, 5]  # 重试间隔（秒）

class ResponseFormat(BaseModel):
    """标准化响应格式，便于与A2A协议对接"""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str
    references: Optional[List[Dict[str, Any]]] = None

class RagFlowAgent:
    """RagFlow代理实现，负责与RagFlow API交互"""
    
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(self, chat_id: Optional[str] = None, agent_id: Optional[str] = None):
        """
        初始化RagFlow代理
        
        Args:
            chat_id: RagFlow中的chat_id，用于与Chat Assistant交互
            agent_id: RagFlow中的agent_id，用于与Agent交互
        
        注意：必须提供chat_id或agent_id之一
        """
        # 获取API密钥
        self.api_key = os.environ.get("RAGFLOW_API_KEY")
        if not self.api_key:
            raise ValueError("RAGFLOW_API_KEY环境变量未设置")
            
        # 获取API URL，优先使用RAGFLOW_API_URL，如果没有则使用RAGFLOW_ENDPOINT
        self.base_url = os.environ.get("RAGFLOW_API_URL") or os.environ.get("RAGFLOW_ENDPOINT") or "https://api.ragflow.ai"
        if not (os.environ.get("RAGFLOW_API_URL") or os.environ.get("RAGFLOW_ENDPOINT")):
            logger.warning(f"未设置RAGFLOW_API_URL或RAGFLOW_ENDPOINT环境变量，使用默认值: {self.base_url}")
        
        # 如果没有提供chat_id，尝试从环境变量中获取
        if not chat_id and not agent_id:
            chat_assistants = os.environ.get("chat_assistants")
            if chat_assistants:
                # 如果有多个ID用逗号分隔，取第一个
                chat_id = chat_assistants.split(",")[0].strip()
                logger.info(f"从环境变量获取chat_id: {chat_id}")
            
        # 确认至少提供了一个ID
        if not chat_id and not agent_id:
            raise ValueError("必须提供chat_id或agent_id之一")
            
        self.chat_id = chat_id
        self.agent_id = agent_id
        self.is_agent_mode = agent_id is not None
        
        logger.info(f"初始化RagFlow代理: {'Agent模式' if self.is_agent_mode else 'Chat模式'}, ID: {self.agent_id or self.chat_id}")
        logger.info(f"使用RagFlow API: {self.base_url}")
        
        # 使用会话管理器替代内存字典
        self.session_manager = SessionManager()
        
    def get_headers(self):
        """获取API请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def create_session(self, session_id: str) -> str:
        """
        创建RagFlow会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            RagFlow会话ID
        """
        # 先尝试从会话管理器获取
        ragflow_session_id = self.session_manager.get_session(session_id)
        if ragflow_session_id:
            logger.info(f"从持久化存储中恢复会话: A2A会话ID {session_id} -> RagFlow会话ID {ragflow_session_id}")
            return ragflow_session_id
            
        endpoint = None
        if self.is_agent_mode:
            endpoint = f"/api/v1/agents/{self.agent_id}/sessions"
        else:
            endpoint = f"/api/v1/chats/{self.chat_id}/sessions"
            
        # 添加重试逻辑
        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        headers=self.get_headers(),
                        json={"name": f"A2A Session {session_id}"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("code") == 0:
                            # 存储映射关系到持久化存储
                            ragflow_session_id = data["data"]["id"]
                            agent_type = "agent" if self.is_agent_mode else "chat"
                            agent_id = self.agent_id if self.is_agent_mode else self.chat_id
                            
                            # 保存到会话管理器
                            if self.session_manager.save_session(session_id, ragflow_session_id, agent_type, agent_id):
                                logger.info(f"创建RagFlow会话成功并持久化: A2A会话ID {session_id} -> RagFlow会话ID {ragflow_session_id}")
                            else:
                                logger.warning(f"会话持久化失败: A2A会话ID {session_id} -> RagFlow会话ID {ragflow_session_id}")
                                
                            return ragflow_session_id
                    
                    # 如果是500或503错误，重试
                    if response.status_code in [429, 500, 502, 503, 504]:
                        retry_delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF)-1)]
                        logger.warning(f"创建会话失败，HTTP {response.status_code}，{retry_delay}秒后重试 ({attempt+1}/{MAX_RETRIES})")
                        await asyncio.sleep(retry_delay)
                        continue
                        
                    # 其他错误，直接失败
                    logger.error(f"创建会话失败: {response.text}")
                    raise ValueError(f"创建会话失败: {response.text}")
            
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < MAX_RETRIES - 1:
                    retry_delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF)-1)]
                    logger.warning(f"连接错误: {str(e)}，{retry_delay}秒后重试 ({attempt+1}/{MAX_RETRIES})")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"创建会话失败，连接错误: {str(e)}")
                    raise ValueError(f"创建会话失败，连接错误: {str(e)}")
            
        # 所有重试都失败
        raise ValueError("创建会话失败：超过最大重试次数")
    
    async def invoke(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        调用RagFlow API进行对话
        
        Args:
            query: 用户查询
            session_id: 会话ID
            
        Returns:
            标准化的响应结果
        """
        ragflow_session_id = await self.create_session(session_id)
        
        endpoint = None
        payload = {"question": query, "stream": False}
        
        if self.is_agent_mode:
            endpoint = f"/api/v1/agents/{self.agent_id}/completions"
        else:
            endpoint = f"/api/v1/chats/{self.chat_id}/completions"
            
        payload["session_id"] = ragflow_session_id
        
        logger.info(f"发送非流式请求: {query}")
        
        # 添加重试逻辑
        for attempt in range(MAX_RETRIES):
            try:
                # 增加超时时间
                timeout = httpx.Timeout(DEFAULT_TIMEOUT, connect=30.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        headers=self.get_headers(),
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("code") == 0:
                            # 处理结果
                            result = data.get("data", {})
                            answer = result.get("answer", "")
                            references = result.get("reference", {})
                            
                            logger.info(f"收到非流式回答: {answer[:100]}...")
                            
                            # 返回标准格式
                            return {
                                "is_task_complete": True,
                                "require_user_input": False,
                                "content": answer,
                                "references": references
                            }
                    
                    # 如果是临时错误，重试
                    if response.status_code in [429, 500, 502, 503, 504]:
                        retry_delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF)-1)]
                        logger.warning(f"对话请求失败，HTTP {response.status_code}，{retry_delay}秒后重试 ({attempt+1}/{MAX_RETRIES})")
                        await asyncio.sleep(retry_delay)
                        continue
                        
                    # 其他错误
                    logger.error(f"对话请求失败: HTTP {response.status_code} - {response.text}")
                    return {
                        "is_task_complete": False,
                        "require_user_input": True,
                        "content": f"与RagFlow服务通信失败: HTTP {response.status_code}",
                        "references": None
                    }
                    
            except httpx.TimeoutException as e:
                if attempt < MAX_RETRIES - 1:
                    retry_delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF)-1)]
                    logger.warning(f"请求超时: {str(e)}，{retry_delay}秒后重试 ({attempt+1}/{MAX_RETRIES})")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"对话请求失败，请求超时: {str(e)}")
                    return {
                        "is_task_complete": False,
                        "require_user_input": True,
                        "content": "RagFlow服务响应超时，请尝试更简短的问题，或稍后再试",
                        "references": None
                    }
                    
            except httpx.ConnectError as e:
                if attempt < MAX_RETRIES - 1:
                    retry_delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF)-1)]
                    logger.warning(f"连接错误: {str(e)}，{retry_delay}秒后重试 ({attempt+1}/{MAX_RETRIES})")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"对话请求失败，连接错误: {str(e)}")
                    return {
                        "is_task_complete": False,
                        "require_user_input": True,
                        "content": f"无法连接到RagFlow服务: {str(e)}",
                        "references": None
                    }
                    
            except Exception as e:
                logger.error(f"对话请求失败，未知错误: {str(e)}")
                logger.exception(e)
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": f"调用RagFlow服务时出现未知错误: {str(e)}",
                    "references": None
                }
        
        # 所有重试都失败
        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "达到最大重试次数，无法完成请求，请稍后再试",
            "references": None
        }
    
    async def stream(self, query: str, session_id: str) -> AsyncIterable[Dict[str, Any]]:
        """
        流式调用RagFlow API
        
        Args:
            query: 用户查询
            session_id: 会话ID
            
        Yields:
            流式标准化响应结果
        """
        ragflow_session_id = await self.create_session(session_id)
        
        endpoint = None
        payload = {"question": query, "stream": True}
        
        if self.is_agent_mode:
            endpoint = f"/api/v1/agents/{self.agent_id}/completions"
        else:
            endpoint = f"/api/v1/chats/{self.chat_id}/completions"
            
        payload["session_id"] = ragflow_session_id
        
        logger.info(f"发送流式请求: {query}")
        
        # 第一个中间状态
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "正在查询知识库...",
            "references": None
        }
        
        # 重试逻辑
        for attempt in range(MAX_RETRIES):
            try:
                # 增加流式请求的超时时间
                timeout = httpx.Timeout(DEFAULT_TIMEOUT, connect=30.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}{endpoint}",
                        headers=self.get_headers(),
                        json=payload
                    ) as response:
                        if response.status_code != 200:
                            # 如果是临时错误，重试
                            if response.status_code in [429, 500, 502, 503, 504] and attempt < MAX_RETRIES - 1:
                                error_text = await response.text()
                                retry_delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF)-1)]
                                logger.warning(f"流式对话请求失败，HTTP {response.status_code}，{retry_delay}秒后重试 ({attempt+1}/{MAX_RETRIES}): {error_text}")
                                
                                yield {
                                    "is_task_complete": False,
                                    "require_user_input": False,
                                    "content": f"正在重试请求... ({attempt+1}/{MAX_RETRIES})",
                                    "references": None
                                }
                                
                                await asyncio.sleep(retry_delay)
                                continue
                            
                            # 其他错误直接返回
                            error_text = await response.text()
                            logger.error(f"流式对话请求失败: HTTP {response.status_code} - {error_text}")
                            yield {
                                "is_task_complete": False,
                                "require_user_input": True,
                                "content": f"与RagFlow服务通信失败: HTTP {response.status_code}",
                                "references": None
                            }
                            return
                        
                        accumulated_answer = ""
                        references = None
                        has_error = False
                        
                        # 解析SSE流
                        async for line in response.aiter_lines():
                            if not line or not line.startswith("data:"):
                                continue
                            
                            try:
                                data_str = line[5:].strip()
                                data = json.loads(data_str)
                                
                                # 检查是否是最后一个事件
                                if data.get("data") is True:
                                    logger.info("流式回答完成")
                                    break
                                
                                # 检查是否有错误
                                if data.get("code") != 0:
                                    has_error = True
                                    error_msg = data.get("message", "未知错误")
                                    logger.error(f"流式回答错误: {error_msg}")
                                    yield {
                                        "is_task_complete": False,
                                        "require_user_input": True,
                                        "content": f"RagFlow服务返回错误: {error_msg}",
                                        "references": None
                                    }
                                    break
                                
                                result = data.get("data", {})
                                
                                # 更新累积的回答
                                if "answer" in result:
                                    accumulated_answer = result["answer"]
                                    
                                    # 只有当有实质性更新时才发送
                                    if len(accumulated_answer) > 0:
                                        logger.debug(f"流式回答更新: {accumulated_answer[-50:]}...")
                                        yield {
                                            "is_task_complete": False, 
                                            "require_user_input": False,
                                            "content": accumulated_answer,
                                            "references": None
                                        }
                                
                                # 获取引用信息
                                if "reference" in result and result["reference"]:
                                    references = result["reference"]
                            
                            except json.JSONDecodeError:
                                logger.warning(f"解析SSE数据失败: {line}")
                                continue
                        
                        # 最终结果
                        if not has_error:
                            logger.info(f"流式回答最终结果: {accumulated_answer[:100]}...")
                            if references:
                                logger.info(f"包含 {len(references.get('chunks', []))} 个引用")
                            yield {
                                "is_task_complete": True,
                                "require_user_input": False,
                                "content": accumulated_answer,
                                "references": references
                            }
            except Exception as e:
                logger.error(f"流式请求异常: {str(e)}")
                yield {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": f"流式请求异常: {str(e)}",
                    "references": None
                } 