#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型定义
用于DatabaseTaskManager的ORM映射
"""
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class TaskTable(Base):
    """任务表"""
    __tablename__ = 'tasks'
    
    id = Column(String(50), primary_key=True)
    session_id = Column(String(50), nullable=True)
    status_state = Column(String(20), nullable=False)
    status_message = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    @classmethod
    def create_from_task(cls, task):
        """从Task对象创建数据库记录"""
        status_message = task.status.message.model_dump() if task.status.message else None
        return cls(
            id=task.id,
            session_id=task.sessionId,
            status_state=task.status.state,
            status_message=status_message
        )

class MessageTable(Base):
    """消息表"""
    __tablename__ = 'messages'
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(50), ForeignKey('tasks.id'), nullable=False)
    content = Column(JSON, nullable=False)  # 存储整个Message对象
    is_history = Column(Boolean, default=True)  # 是否为历史消息
    created_at = Column(DateTime, server_default=func.now())
    
    @classmethod
    def create_from_message(cls, task_id, message, is_history=True):
        """从Message对象创建数据库记录"""
        return cls(
            id=str(uuid.uuid4()),
            task_id=task_id,
            content=message.model_dump(),
            is_history=is_history
        )

class ArtifactTable(Base):
    """构件表"""
    __tablename__ = 'artifacts'
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(50), ForeignKey('tasks.id'), nullable=False)
    content = Column(JSON, nullable=False)  # 存储整个Artifact对象
    created_at = Column(DateTime, server_default=func.now())
    
    @classmethod
    def create_from_artifact(cls, task_id, artifact):
        """从Artifact对象创建数据库记录"""
        return cls(
            id=str(uuid.uuid4()),
            task_id=task_id,
            content=artifact.model_dump()
        )

class PushNotificationTable(Base):
    """推送通知配置表"""
    __tablename__ = 'push_notifications'
    
    task_id = Column(String(50), ForeignKey('tasks.id'), primary_key=True)
    config = Column(JSON, nullable=False)  # 存储整个PushNotificationConfig对象
    created_at = Column(DateTime, server_default=func.now())
    
    @classmethod
    def create_from_config(cls, task_id, config):
        """从PushNotificationConfig对象创建数据库记录"""
        return cls(
            task_id=task_id,
            config=config.model_dump()
        ) 