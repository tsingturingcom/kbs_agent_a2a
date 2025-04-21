#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RagFlow任务管理器
使用组合模式，代理TaskManager接口，添加RagFlow特定的业务逻辑
"""
import sys
import os
import asyncio

# 添加项目根目录到Python路径（如果尚未添加）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))  # 只需上溯两级到项目根目录
if project_root not in sys.path:
    sys.path.insert(0, project_root)  # 直接添加项目根目录

from typing import AsyncIterable, Union, Optional
from common.types import (
    SendTaskRequest,
    TaskSendParams,
    Message,
    TaskStatus,
    Artifact,
    TextPart,
    TaskState,
    SendTaskResponse,
    InternalError,
    JSONRPCResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    Task,
    TaskIdParams,
    PushNotificationConfig,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse,
    GetTaskPushNotificationRequest,
    GetTaskPushNotificationResponse,
    GetTaskRequest,
    GetTaskResponse,
    CancelTaskRequest,
    CancelTaskResponse,
    TaskResubscriptionRequest,
    InvalidParamsError,
)
from common.server.task_manager import TaskManager
from agents.ragflow.agent import RagFlowAgent
from common.utils.push_notification_auth import PushNotificationSenderAuth
import common.server.utils as utils
import logging
import traceback
import json

logger = logging.getLogger(__name__)

class RagFlowTaskManager(TaskManager):
    """
    RagFlow任务管理器，将A2A协议请求映射到RagFlow代理
    
    使用组合模式，代理TaskManager接口，添加RagFlow特定的业务逻辑，
    存储实现由任意TaskManager实现提供
    """
    
    def __init__(self, 
                task_manager: TaskManager, 
                agent: RagFlowAgent, 
                notification_sender_auth: PushNotificationSenderAuth):
        """
        初始化RagFlow任务管理器
        
        Args:
            task_manager: 存储任务的管理器实例（可以是内存版或数据库版）
            agent: RagFlow代理实例
            notification_sender_auth: 推送通知认证
        """
        self.task_manager = task_manager
        self.agent = agent
        self.notification_sender_auth = notification_sender_auth

    # 代理基础方法到底层task_manager
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        """代理到底层任务管理器"""
        return await self.task_manager.on_get_task(request)

    async def on_cancel_task(self, request: CancelTaskRequest) -> CancelTaskResponse:
        """代理到底层任务管理器"""
        return await self.task_manager.on_cancel_task(request)

    async def on_set_task_push_notification(
        self, request: SetTaskPushNotificationRequest
    ) -> SetTaskPushNotificationResponse:
        """代理到底层任务管理器"""
        return await self.task_manager.on_set_task_push_notification(request)

    async def on_get_task_push_notification(
        self, request: GetTaskPushNotificationRequest
    ) -> GetTaskPushNotificationResponse:
        """代理到底层任务管理器"""
        return await self.task_manager.on_get_task_push_notification(request)

    # 代理存储相关方法
    async def has_push_notification_info(self, task_id: str) -> bool:
        """查询是否存在推送通知配置"""
        return await self.task_manager.has_push_notification_info(task_id)

    async def get_push_notification_info(self, task_id: str) -> PushNotificationConfig:
        """获取推送通知配置"""
        return await self.task_manager.get_push_notification_info(task_id)

    async def upsert_task(self, task_send_params: TaskSendParams) -> Task:
        """创建或更新任务"""
        return await self.task_manager.upsert_task(task_send_params)

    async def update_store(
        self, task_id: str, status: TaskStatus, artifacts: Optional[list[Artifact]]
    ) -> Task:
        """更新任务存储"""
        return await self.task_manager.update_store(task_id, status, artifacts)

    async def setup_sse_consumer(self, task_id: str, is_resubscribe: bool = False):
        """设置SSE事件消费者"""
        return await self.task_manager.setup_sse_consumer(task_id, is_resubscribe)

    async def enqueue_events_for_sse(self, task_id, task_update_event):
        """将事件加入SSE队列"""
        await self.task_manager.enqueue_events_for_sse(task_id, task_update_event)

    def dequeue_events_for_sse(self, request_id, task_id, sse_event_queue):
        """从SSE队列获取事件"""
        return self.task_manager.dequeue_events_for_sse(request_id, task_id, sse_event_queue)

    # RagFlow特定业务逻辑实现
    async def _run_streaming_agent(self, request: SendTaskStreamingRequest):
        """运行流式代理，处理流式请求"""
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)

        try:
            async for item in self.agent.stream(query, task_send_params.sessionId):
                is_task_complete = item["is_task_complete"]
                require_user_input = item["require_user_input"]
                artifact = None
                message = None
                references = item.get("references")
                
                # 构建文本部分
                parts = [{"type": "text", "text": item["content"]}]
                
                # 如果有参考资料，添加到内容中
                if references and isinstance(references, dict) and references.get("chunks"):
                    reference_data = {
                        "type": "data",
                        "data": {"references": references}
                    }
                    parts.append(reference_data)
                
                # 根据状态更新任务
                end_stream = False
                if not is_task_complete and not require_user_input:
                    task_state = TaskState.WORKING
                    message = Message(role="agent", parts=parts)
                elif require_user_input:
                    task_state = TaskState.INPUT_REQUIRED
                    message = Message(role="agent", parts=parts)
                    end_stream = True
                else:
                    task_state = TaskState.COMPLETED
                    artifact = Artifact(parts=parts, index=0, append=False)
                    end_stream = True

                # 更新任务状态
                task_status = TaskStatus(state=task_state, message=message)
                latest_task = await self.update_store(
                    task_send_params.id,
                    task_status,
                    None if artifact is None else [artifact],
                )
                
                # 发送推送通知
                await self.send_task_notification(latest_task)

                # 如果有构件，发送构件更新事件
                if artifact:
                    task_artifact_update_event = TaskArtifactUpdateEvent(
                        id=task_send_params.id, artifact=artifact
                    )
                    await self.enqueue_events_for_sse(
                        task_send_params.id, task_artifact_update_event
                    )                    

                # 发送任务状态更新事件
                task_update_event = TaskStatusUpdateEvent(
                    id=task_send_params.id, status=task_status, final=end_stream
                )
                await self.enqueue_events_for_sse(
                    task_send_params.id, task_update_event
                )

        except Exception as e:
            logger.error(f"流式响应过程中发生错误: {e}")
            logger.error(traceback.format_exc())
            await self.enqueue_events_for_sse(
                task_send_params.id,
                InternalError(message=f"流式响应过程中发生错误: {e}")                
            )

    def _validate_request(
        self, request: Union[SendTaskRequest, SendTaskStreamingRequest]
    ) -> JSONRPCResponse | None:
        """验证请求的合法性"""
        task_send_params: TaskSendParams = request.params
        
        # 验证内容类型兼容性
        if not utils.are_modalities_compatible(
            task_send_params.acceptedOutputModes, RagFlowAgent.SUPPORTED_CONTENT_TYPES
        ):
            logger.warning(
                "不支持的输出模式. 接收到 %s, 支持 %s",
                task_send_params.acceptedOutputModes,
                RagFlowAgent.SUPPORTED_CONTENT_TYPES,
            )
            return utils.new_incompatible_types_error(request.id)
        
        # 验证推送通知URL
        if task_send_params.pushNotification and not task_send_params.pushNotification.url:
            logger.warning("缺少推送通知URL")
            return JSONRPCResponse(id=request.id, error=InvalidParamsError(message="缺少推送通知URL"))
        
        return None
        
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """处理发送任务请求"""
        # 验证请求
        validation_error = self._validate_request(request)
        if validation_error:
            return SendTaskResponse(id=request.id, error=validation_error.error)
        
        # 设置推送通知
        if request.params.pushNotification:
            if not await self.set_push_notification_info(request.params.id, request.params.pushNotification):
                return SendTaskResponse(id=request.id, error=InvalidParamsError(message="推送通知URL无效"))

        # 更新任务状态为处理中
        await self.upsert_task(request.params)
        task = await self.update_store(
            request.params.id, TaskStatus(state=TaskState.WORKING), None
        )
        await self.send_task_notification(task)

        # 调用代理处理请求
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)
        try:
            agent_response = await self.agent.invoke(query, task_send_params.sessionId)
            
            # 检查代理响应是否成功
            if not agent_response.get("is_task_complete", False):
                error_msg = agent_response.get("content", "未知错误")
                logger.warning(f"代理响应未完成: {error_msg}")
                
                # 更新任务状态为错误或需要用户输入
                if agent_response.get("require_user_input", False):
                    task_status = TaskStatus(
                        state=TaskState.INPUT_REQUIRED, 
                        message=Message(
                            role="agent",
                            parts=[{"type": "text", "text": error_msg}]
                        )
                    )
                    updated_task = await self.update_store(task_send_params.id, task_status, None)
                    await self.send_task_notification(updated_task)
                    
                    # 返回INPUT_REQUIRED状态
                    return SendTaskResponse(
                        id=request.id,
                        result=updated_task
                    )
                else:
                    # 返回错误
                    return JSONRPCResponse(
                        id=request.id,
                        error=InternalError(message=error_msg)
                    )
            
        except Exception as e:
            logger.error(f"调用代理时出错: {e}")
            logger.error(traceback.format_exc())
            
            # 更新任务状态为错误
            error_message = f"调用代理时出错: {str(e)}"
            task_status = TaskStatus(
                state=TaskState.ERROR, 
                message=Message(
                    role="agent",
                    parts=[{"type": "text", "text": "处理您的请求时发生错误，请稍后再试或尝试更简单的问题。"}]
                )
            )
            updated_task = await self.update_store(task_send_params.id, task_status, None)
            await self.send_task_notification(updated_task)
            
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(message=error_message)
            )
            
        # 处理代理响应
        return await self._process_agent_response(
            request, agent_response
        )

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """处理流式任务请求"""
        try:
            # 验证请求
            error = self._validate_request(request)
            if error:
                return error

            # 创建任务
            await self.upsert_task(request.params)

            # 设置推送通知
            if request.params.pushNotification:
                if not await self.set_push_notification_info(request.params.id, request.params.pushNotification):
                    return JSONRPCResponse(id=request.id, error=InvalidParamsError(message="推送通知URL无效"))

            # 设置SSE事件队列
            task_send_params: TaskSendParams = request.params
            sse_event_queue = await self.setup_sse_consumer(task_send_params.id, False)            

            # 异步启动流式处理
            asyncio.create_task(self._run_streaming_agent(request))

            # 返回事件队列
            return self.dequeue_events_for_sse(
                request.id, task_send_params.id, sse_event_queue
            )
        except Exception as e:
            logger.error(f"SSE流处理时出错: {e}")
            logger.error(traceback.format_exc())
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message=f"流式响应处理时出错: {e}"
                ),
            )

    async def _process_agent_response(
        self, request: SendTaskRequest, agent_response: dict
    ) -> SendTaskResponse:
        """处理代理响应，将其转换为A2A格式"""
        task_send_params: TaskSendParams = request.params
        
        # 检查响应有效性
        if not isinstance(agent_response, dict):
            logger.error(f"代理响应格式错误: {agent_response}")
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(message="代理响应格式错误")
            )
        
        # 提取响应内容
        content = agent_response.get("content", "")
        references = agent_response.get("references", None)
        
        # 构建消息部分
        parts = [{"type": "text", "text": content}]
        
        # 如果有参考资料，添加数据部分
        if references and isinstance(references, dict) and references.get("chunks"):
            reference_data = {
                "type": "data",
                "data": {"references": references}
            }
            parts.append(reference_data)
        
        # 创建构件
        artifact = Artifact(parts=parts, index=0, append=False)
        
        # 更新任务状态为完成
        task_status = TaskStatus(state=TaskState.COMPLETED)
        updated_task = await self.update_store(task_send_params.id, task_status, [artifact])
        
        # 发送通知
        await self.send_task_notification(updated_task)
        
        # 返回响应
        return SendTaskResponse(
            id=request.id,
            result=updated_task
        )
    
    def _get_user_query(self, task_send_params: TaskSendParams) -> str:
        """从任务参数中提取用户查询"""
        part = task_send_params.message.parts[0]
        if not isinstance(part, TextPart):
            raise ValueError("仅支持文本部分")
        return part.text
    
    async def send_task_notification(self, task: Task):
        """发送任务推送通知"""
        if not await self.has_push_notification_info(task.id):
            logger.debug(f"未找到任务 {task.id} 的推送通知信息")
            return
        push_info = await self.get_push_notification_info(task.id)

        logger.info(f"发送任务 {task.id} 通知 => {task.status.state}")
        await self.notification_sender_auth.send_push_notification(
            push_info.url,
            data=task.model_dump(exclude_none=True)
        )

    async def on_resubscribe_to_task(
        self, request: TaskResubscriptionRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """处理重新订阅任务的请求"""
        task_id_params: TaskIdParams = request.params
        try:
            sse_event_queue = await self.setup_sse_consumer(task_id_params.id, True)
            return self.dequeue_events_for_sse(request.id, task_id_params.id, sse_event_queue)
        except Exception as e:
            logger.error(f"重新连接到SSE流时出错: {e}")
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message=f"重新连接到流时出错: {e}"
                ),
            )
    
    async def set_push_notification_info(self, task_id: str, push_notification_config: PushNotificationConfig):
        """设置推送通知信息"""
        # 验证通知URL所有权
        is_verified = await self.notification_sender_auth.verify_push_notification_url(push_notification_config.url)
        if not is_verified:
            return False
        
        await self.task_manager.set_push_notification_info(task_id, push_notification_config)
        return True 