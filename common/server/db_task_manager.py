#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库持久化任务管理器
实现与InMemoryTaskManager功能一致的数据库存储版本
"""
from typing import Union, AsyncIterable, List, Optional
import asyncio
import logging
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete
from sqlalchemy.future import select

from common.types import (
    Task, Message, TaskStatus, Artifact, PushNotificationConfig,
    JSONRPCResponse, TaskIdParams, TaskQueryParams, 
    GetTaskRequest, TaskNotFoundError, SendTaskRequest, 
    CancelTaskRequest, TaskNotCancelableError,
    SetTaskPushNotificationRequest, GetTaskPushNotificationRequest,
    GetTaskResponse, CancelTaskResponse, SendTaskResponse,
    SetTaskPushNotificationResponse, GetTaskPushNotificationResponse,
    PushNotificationNotSupportedError, TaskSendParams,
    TaskState, TaskResubscriptionRequest, SendTaskStreamingRequest,
    SendTaskStreamingResponse, TaskStatusUpdateEvent, JSONRPCError,
    TaskPushNotificationConfig, InternalError
)
from common.server.task_manager import TaskManager
from common.server.models import (
    Base, TaskTable, MessageTable, ArtifactTable, PushNotificationTable
)
from common.server.utils import new_not_implemented_error

logger = logging.getLogger(__name__)

class DatabaseTaskManager(TaskManager):
    """
    数据库持久化任务管理器
    使用SQLAlchemy ORM进行数据存储和检索
    保持与InMemoryTaskManager相同的接口和行为
    """
    
    def __init__(self, db_url: str):
        """
        初始化数据库任务管理器
        
        Args:
            db_url: 数据库连接URL，如 "sqlite+aiosqlite:///tasks.db"
        """
        self.engine = create_async_engine(db_url)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        # 用于并发控制的锁
        self.lock = asyncio.Lock()
        self.subscriber_lock = asyncio.Lock()
        # SSE订阅者队列
        self.task_sse_subscribers: dict[str, List[asyncio.Queue]] = {}
        # 缓存以减少数据库查询
        self._cache = {}
        
    async def initialize(self):
        """初始化数据库表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表初始化完成")
            
    async def _build_task_from_db(
        self, session: AsyncSession, task_row: TaskTable, history_length: Optional[int] = None
    ) -> Task:
        """
        从数据库记录构建Task对象
        
        Args:
            session: 数据库会话
            task_row: 任务表记录
            history_length: 历史消息长度限制
            
        Returns:
            构建的Task对象
        """
        # 查询消息记录
        msg_result = await session.execute(
            select(MessageTable).where(MessageTable.task_id == task_row.id)
        )
        message_rows = msg_result.scalars().all()
        
        # 查询构件记录
        artifacts_result = await session.execute(
            select(ArtifactTable).where(ArtifactTable.task_id == task_row.id)
        )
        artifact_rows = artifacts_result.scalars().all()
        
        # 构建消息列表
        messages = []
        history = []
        
        for msg_row in message_rows:
            msg_content = msg_row.content
            message = Message.model_validate(msg_content)
            
            if msg_row.is_history:
                history.append(message)
        
        # 应用历史长度限制
        if history_length is not None and history_length > 0 and len(history) > 0:
            history = history[-history_length:]
        
        # 构建状态对象
        status = TaskStatus(state=task_row.status_state)
        if task_row.status_message:
            status.message = Message.model_validate(task_row.status_message)
        
        # 构建构件列表
        artifacts = None
        if artifact_rows:
            artifacts = []
            for artifact_row in artifact_rows:
                artifact = Artifact.model_validate(artifact_row.content)
                artifacts.append(artifact)
        
        # 构建完整Task对象
        task = Task(
            id=task_row.id,
            sessionId=task_row.session_id,
            status=status,
            artifacts=artifacts,
            history=history
        )
        
        return task
        
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        """
        获取任务信息
        
        Args:
            request: 获取任务请求
            
        Returns:
            任务信息响应
        """
        logger.info(f"获取任务 {request.params.id}")
        task_query_params: TaskQueryParams = request.params
        
        try:
            async with self.async_session() as session:
                # 查询任务基本信息
                task_result = await session.execute(
                    select(TaskTable).where(TaskTable.id == task_query_params.id)
                )
                task_row = task_result.scalar_one_or_none()
                
                if not task_row:
                    return GetTaskResponse(id=request.id, error=TaskNotFoundError())
                
                # 构建完整Task对象
                task = await self._build_task_from_db(
                    session, task_row, task_query_params.historyLength
                )
                
            return GetTaskResponse(id=request.id, result=task)
        except Exception as e:
            logger.error(f"获取任务时出错: {e}")
            return GetTaskResponse(
                id=request.id,
                error=InternalError(message=f"获取任务时出错: {str(e)}")
            )
    
    async def on_cancel_task(self, request: CancelTaskRequest) -> CancelTaskResponse:
        """
        取消任务
        
        Args:
            request: 取消任务请求
            
        Returns:
            取消任务响应
        """
        logger.info(f"取消任务 {request.params.id}")
        task_id_params: TaskIdParams = request.params
        
        try:
            async with self.async_session() as session:
                # 查询任务是否存在
                task_result = await session.execute(
                    select(TaskTable).where(TaskTable.id == task_id_params.id)
                )
                task_row = task_result.scalar_one_or_none()
                
                if not task_row:
                    return CancelTaskResponse(id=request.id, error=TaskNotFoundError())
                
            # 当前实现不支持取消，与InMemoryTaskManager保持一致
            return CancelTaskResponse(id=request.id, error=TaskNotCancelableError())
        except Exception as e:
            logger.error(f"取消任务时出错: {e}")
            return CancelTaskResponse(
                id=request.id,
                error=InternalError(message=f"取消任务时出错: {str(e)}")
            )
    
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        发送任务请求的抽象方法，子类必须实现
        """
        # 抽象方法，由子类实现
        pass
    
    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> Union[AsyncIterable[SendTaskStreamingResponse], JSONRPCResponse]:
        """
        发送流式任务请求的抽象方法，子类必须实现
        """
        # 抽象方法，由子类实现
        pass
    
    async def set_push_notification_info(self, task_id: str, notification_config: PushNotificationConfig):
        """
        设置任务推送通知信息
        
        Args:
            task_id: 任务ID
            notification_config: 推送通知配置
        """
        async with self.lock:
            async with self.async_session() as session:
                async with session.begin():
                    # 检查任务是否存在
                    task_result = await session.execute(
                        select(TaskTable).where(TaskTable.id == task_id)
                    )
                    task_row = task_result.scalar_one_or_none()
                    
                    if not task_row:
                        raise ValueError(f"Task not found for {task_id}")
                    
                    # 查询是否已存在推送配置
                    notification_result = await session.execute(
                        select(PushNotificationTable).where(
                            PushNotificationTable.task_id == task_id
                        )
                    )
                    notification_row = notification_result.scalar_one_or_none()
                    
                    if notification_row:
                        # 更新现有配置
                        notification_row.config = notification_config.model_dump()
                    else:
                        # 创建新配置
                        new_notification = PushNotificationTable.create_from_config(
                            task_id, notification_config
                        )
                        session.add(new_notification)
    
    async def get_push_notification_info(self, task_id: str) -> PushNotificationConfig:
        """
        获取任务推送通知信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            推送通知配置
        """
        async with self.lock:
            async with self.async_session() as session:
                # 检查任务是否存在
                task_result = await session.execute(
                    select(TaskTable).where(TaskTable.id == task_id)
                )
                task_row = task_result.scalar_one_or_none()
                
                if not task_row:
                    raise ValueError(f"Task not found for {task_id}")
                
                # 获取推送配置
                notification_result = await session.execute(
                    select(PushNotificationTable).where(
                        PushNotificationTable.task_id == task_id
                    )
                )
                notification_row = notification_result.scalar_one_or_none()
                
                if not notification_row:
                    raise ValueError(f"Push notification not found for {task_id}")
                
                return PushNotificationConfig.model_validate(notification_row.config)
    
    async def has_push_notification_info(self, task_id: str) -> bool:
        """
        检查任务是否有推送通知信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否存在推送通知配置
        """
        async with self.lock:
            async with self.async_session() as session:
                notification_result = await session.execute(
                    select(PushNotificationTable).where(
                        PushNotificationTable.task_id == task_id
                    )
                )
                notification_row = notification_result.scalar_one_or_none()
                
                return notification_row is not None
    
    async def on_set_task_push_notification(
        self, request: SetTaskPushNotificationRequest
    ) -> SetTaskPushNotificationResponse:
        """
        设置任务推送通知
        
        Args:
            request: 设置推送通知请求
            
        Returns:
            设置推送通知响应
        """
        logger.info(f"设置任务推送通知 {request.params.id}")
        task_notification_params: TaskPushNotificationConfig = request.params
        
        try:
            await self.set_push_notification_info(
                task_notification_params.id, 
                task_notification_params.pushNotificationConfig
            )
        except Exception as e:
            logger.error(f"设置推送通知信息时出错: {e}")
            return JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message="设置推送通知信息时出错"
                ),
            )
            
        return SetTaskPushNotificationResponse(id=request.id, result=task_notification_params)
    
    async def on_get_task_push_notification(
        self, request: GetTaskPushNotificationRequest
    ) -> GetTaskPushNotificationResponse:
        """
        获取任务推送通知
        
        Args:
            request: 获取推送通知请求
            
        Returns:
            获取推送通知响应
        """
        logger.info(f"获取任务推送通知 {request.params.id}")
        task_params: TaskIdParams = request.params
        
        try:
            notification_info = await self.get_push_notification_info(task_params.id)
        except Exception as e:
            logger.error(f"获取推送通知信息时出错: {e}")
            return GetTaskPushNotificationResponse(
                id=request.id,
                error=InternalError(
                    message="获取推送通知信息时出错"
                ),
            )
        
        return GetTaskPushNotificationResponse(
            id=request.id, 
            result=TaskPushNotificationConfig(
                id=task_params.id, 
                pushNotificationConfig=notification_info
            )
        )
    
    async def upsert_task(self, task_send_params: TaskSendParams) -> Task:
        """
        创建或更新任务
        
        Args:
            task_send_params: 任务发送参数
            
        Returns:
            更新后的任务对象
        """
        logger.info(f"创建/更新任务 {task_send_params.id}")
        
        async with self.lock:
            async with self.async_session() as session:
                async with session.begin():
                    # 查询任务是否存在
                    task_result = await session.execute(
                        select(TaskTable).where(TaskTable.id == task_send_params.id)
                    )
                    task_row = task_result.scalar_one_or_none()
                    
                    if not task_row:
                        # 创建新任务
                        new_task = Task(
                            id=task_send_params.id,
                            sessionId=task_send_params.sessionId,
                            messages=[task_send_params.message],
                            status=TaskStatus(state=TaskState.SUBMITTED),
                            history=[task_send_params.message],
                        )
                        
                        # 保存到数据库
                        task_db = TaskTable.create_from_task(new_task)
                        session.add(task_db)
                        
                        # 保存消息
                        message_db = MessageTable.create_from_message(
                            task_send_params.id, task_send_params.message
                        )
                        session.add(message_db)
                        
                        task = new_task
                    else:
                        # 获取现有任务
                        task = await self._build_task_from_db(session, task_row)
                        
                        # 添加新消息到历史
                        message_db = MessageTable.create_from_message(
                            task_send_params.id, task_send_params.message
                        )
                        session.add(message_db)
                        
                        # 更新任务对象
                        if task.history is None:
                            task.history = []
                        task.history.append(task_send_params.message)
                
                return task
    
    async def on_resubscribe_to_task(
        self, request: TaskResubscriptionRequest
    ) -> Union[AsyncIterable[SendTaskStreamingResponse], JSONRPCResponse]:
        """
        重新订阅任务
        
        Args:
            request: 重新订阅请求
            
        Returns:
            任务流式响应或错误
        """
        return new_not_implemented_error(request.id)
    
    async def update_store(
        self, task_id: str, status: TaskStatus, artifacts: Optional[list[Artifact]]
    ) -> Task:
        """
        更新任务存储
        
        Args:
            task_id: 任务ID
            status: 新的任务状态
            artifacts: 新的构件列表
            
        Returns:
            更新后的任务对象
        """
        async with self.lock:
            async with self.async_session() as session:
                async with session.begin():
                    # 查询任务是否存在
                    task_result = await session.execute(
                        select(TaskTable).where(TaskTable.id == task_id)
                    )
                    task_row = task_result.scalar_one_or_none()
                    
                    if not task_row:
                        logger.error(f"找不到任务 {task_id} 以更新")
                        raise ValueError(f"找不到任务 {task_id}")
                    
                    # 更新任务状态
                    task_row.status_state = status.state
                    if status.message:
                        task_row.status_message = status.message.model_dump()
                        
                        # 添加消息到历史
                        message_db = MessageTable.create_from_message(
                            task_id, status.message
                        )
                        session.add(message_db)
                    
                    # 添加构件
                    if artifacts:
                        for artifact in artifacts:
                            artifact_db = ArtifactTable.create_from_artifact(
                                task_id, artifact
                            )
                            session.add(artifact_db)
                    
                    # 获取更新后的任务
                    await session.flush()
                    task = await self._build_task_from_db(session, task_row)
                    
                    return task
    
    def append_task_history(self, task: Task, historyLength: Optional[int]) -> Task:
        """
        截取任务历史记录
        
        Args:
            task: 任务对象
            historyLength: 历史记录长度限制
            
        Returns:
            修改后的任务对象副本
        """
        new_task = task.model_copy()
        if historyLength is not None and historyLength > 0:
            new_task.history = new_task.history[-historyLength:]
        else:
            new_task.history = []
        
        return new_task
    
    async def setup_sse_consumer(self, task_id: str, is_resubscribe: bool = False) -> asyncio.Queue:
        """
        设置SSE消费者队列
        
        Args:
            task_id: 任务ID
            is_resubscribe: 是否为重新订阅
            
        Returns:
            事件队列
        """
        async with self.subscriber_lock:
            if task_id not in self.task_sse_subscribers:
                if is_resubscribe:
                    raise ValueError("重新订阅找不到任务")
                else:
                    self.task_sse_subscribers[task_id] = []
            
            sse_event_queue = asyncio.Queue(maxsize=0)  # <=0表示无限
            self.task_sse_subscribers[task_id].append(sse_event_queue)
            return sse_event_queue
    
    async def enqueue_events_for_sse(self, task_id: str, task_update_event):
        """
        将事件加入SSE队列
        
        Args:
            task_id: 任务ID
            task_update_event: 任务更新事件
        """
        async with self.subscriber_lock:
            if task_id not in self.task_sse_subscribers:
                return
            
            current_subscribers = self.task_sse_subscribers[task_id]
            for subscriber in current_subscribers:
                await subscriber.put(task_update_event)
    
    async def dequeue_events_for_sse(
        self, request_id, task_id: str, sse_event_queue: asyncio.Queue
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """
        从SSE队列获取事件
        
        Args:
            request_id: 请求ID
            task_id: 任务ID
            sse_event_queue: 事件队列
            
        Returns:
            流式任务响应
        """
        try:
            while True:
                event = await sse_event_queue.get()
                if isinstance(event, JSONRPCError):
                    yield SendTaskStreamingResponse(id=request_id, error=event)
                    break
                
                yield SendTaskStreamingResponse(id=request_id, result=event)
                if isinstance(event, TaskStatusUpdateEvent) and event.final:
                    break
        finally:
            async with self.subscriber_lock:
                if task_id in self.task_sse_subscribers:
                    self.task_sse_subscribers[task_id].remove(sse_event_queue) 