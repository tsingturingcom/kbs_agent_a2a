#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器工厂
用于根据配置创建合适的任务管理器实例
"""
import os
import logging
import pathlib
from typing import Dict, Any, Optional, Type
from common.server.task_manager import TaskManager, InMemoryTaskManager
from common.server.db_task_manager import DatabaseTaskManager

logger = logging.getLogger(__name__)

class TaskManagerFactory:
    """
    任务管理器工厂类
    根据配置创建合适的任务管理器实例
    """
    
    @staticmethod
    async def create_task_manager(config: Dict[str, Any] = None) -> TaskManager:
        """
        创建任务管理器实例
        
        Args:
            config: 配置字典，包含任务管理器类型和相关配置
                   如果为None，则从环境变量读取配置
                   
        Returns:
            任务管理器实例
        """
        if config is None:
            config = {}
            
        # 从环境变量或配置获取存储类型
        storage_type = config.get('storage_type') or os.environ.get('TASK_STORAGE_TYPE', 'memory')
        logger.info(f"使用存储类型: {storage_type}")
        
        if storage_type.lower() == 'database':
            # 从环境变量或配置获取数据库URL
            db_url = config.get('db_url') or os.environ.get('TASK_DB_URL')
            if not db_url:
                # 如果没有URL配置，则使用默认的SQLite数据库
                db_url = "sqlite+aiosqlite:///agents/ragflow/data/tasks.db"
                logger.warning(f"未指定数据库URL，使用默认值: {db_url}")
                
            # 确保SQLite数据库目录存在
            if db_url.startswith('sqlite'):
                # 解析数据库文件路径
                # 格式：sqlite+aiosqlite:///path/to/database.db
                db_path = db_url.split(':///', 1)[1]
                # 创建目录
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    logger.info(f"创建数据库目录: {db_dir}")
                    os.makedirs(db_dir, exist_ok=True)
                
            # 创建数据库任务管理器
            task_manager = DatabaseTaskManager(db_url)
            # 初始化数据库
            await task_manager.initialize()
            logger.info(f"已创建数据库任务管理器，使用 {db_url}")
            return task_manager
        else:
            # 默认使用内存任务管理器
            logger.info("已创建内存任务管理器")
            return InMemoryTaskManager()
            
    @staticmethod
    async def migrate_data(source_manager: TaskManager, target_manager: TaskManager):
        """
        数据迁移工具，将源管理器中的数据迁移到目标管理器
        
        Args:
            source_manager: 源任务管理器
            target_manager: 目标任务管理器
        """
        if isinstance(source_manager, InMemoryTaskManager) and isinstance(target_manager, DatabaseTaskManager):
            logger.info("开始从内存迁移数据到数据库...")
            
            # 获取内存中的任务
            source_tasks = source_manager.tasks
            source_notifications = source_manager.push_notification_infos
            
            # 迁移每个任务
            for task_id, task in source_tasks.items():
                # 创建任务
                await target_manager.upsert_task(
                    TaskSendParams(
                        id=task.id,
                        sessionId=task.sessionId,
                        message=task.history[0] if task.history else None
                    )
                )
                
                # 更新任务状态
                await target_manager.update_store(
                    task_id, 
                    task.status,
                    task.artifacts
                )
                
                # 迁移推送通知
                if task_id in source_notifications:
                    await target_manager.set_push_notification_info(
                        task_id, source_notifications[task_id]
                    )
                    
            logger.info("数据迁移完成")
            
        elif isinstance(source_manager, DatabaseTaskManager) and isinstance(target_manager, InMemoryTaskManager):
            logger.info("从数据库迁移到内存不支持，因为数据库中可能有大量数据")
        else:
            logger.warning("无法识别的迁移类型") 