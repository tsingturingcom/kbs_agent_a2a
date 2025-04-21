#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RagFlow会话管理器
负责管理A2A会话与RagFlow会话的映射关系
使用数据库进行持久化存储，支持多种数据库引擎
"""

import os
import logging
import json
import time
import pathlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import sys

# 添加项目根目录到Python路径（如果尚未添加）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))  # 只需上溯两级到项目根目录
if project_root not in sys.path:
    sys.path.insert(0, project_root)  # 直接添加项目根目录

# SQLAlchemy导入
from sqlalchemy import Column, String, DateTime, Text, create_engine, text, func, select, insert, update, delete
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# dotenv用于加载环境变量
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 创建Base类
Base = declarative_base()

# 定义模型类
class SessionMapping(Base):
    """会话映射表"""
    __tablename__ = 'session_mappings'
    
    a2a_session_id = Column(String(50), primary_key=True)
    ragflow_session_id = Column(String(50), nullable=False)
    agent_type = Column(String(20), nullable=False)  # 'chat' 或 'agent'
    agent_id = Column(String(50), nullable=False)    # chat_id 或 agent_id
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SessionContext(Base):
    """会话上下文表"""
    __tablename__ = 'session_context'
    
    a2a_session_id = Column(String(50), primary_key=True)
    context = Column(Text, nullable=True)  # JSON格式的上下文数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SessionManager:
    """
    RagFlow会话管理器
    负责管理A2A会话ID与RagFlow会话ID的映射关系
    使用数据库进行持久化存储，与任务存储完全独立
    支持多种数据库引擎（SQLite, PostgreSQL, MySQL等）
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化会话管理器
        
        Args:
            db_url: 数据库连接URL，如果为None则从环境变量SESSION_DB_URL读取
                   如果环境变量也未设置，则使用默认的SQLite数据库
        """
        # 从环境变量获取数据库URL
        if db_url is None:
            db_url = os.environ.get("SESSION_DB_URL")
            
        # 如果环境变量未设置，使用默认的SQLite数据库
        if db_url is None:
            # 默认使用data目录下的sessions.db文件
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(current_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "sessions.db")
            db_url = f"sqlite:///{db_path}"
            
        self.db_url = db_url
        logger.info(f"会话管理器使用数据库: {self.db_url}")
        
        # 确保SQLite数据库目录存在
        if db_url.startswith('sqlite'):
            # 解析数据库文件路径
            # 格式：sqlite:///path/to/database.db
            import re
            match = re.match(r'sqlite:///(.+)', db_url)
            if match:
                db_path = match.group(1)
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
        
        # 创建数据库引擎
        self.engine = create_engine(db_url)
        
        # 创建session工厂
        self.Session = sessionmaker(bind=self.engine)
        
        # 初始化数据库
        self._init_db()
        
        # 内存缓存，提高性能
        self._cache = {}
        
    def _init_db(self):
        """初始化数据库表"""
        try:
            # 创建表
            Base.metadata.create_all(self.engine)
            logger.info("会话数据库表初始化完成")
        except SQLAlchemyError as e:
            logger.error(f"初始化会话数据库错误: {e}")
            raise
    
    def get_session(self, a2a_session_id: str) -> Optional[str]:
        """
        获取RagFlow会话ID
        
        Args:
            a2a_session_id: A2A会话ID
            
        Returns:
            RagFlow会话ID，如果不存在则返回None
        """
        # 先检查缓存
        if a2a_session_id in self._cache:
            # 更新最后使用时间
            self._update_last_used(a2a_session_id)
            return self._cache[a2a_session_id]
        
        # 查询数据库
        try:
            with self.Session() as session:
                # 使用SQLAlchemy ORM查询
                stmt = select(SessionMapping.ragflow_session_id).where(
                    SessionMapping.a2a_session_id == a2a_session_id
                )
                result = session.execute(stmt).scalar_one_or_none()
                
                if result:
                    # 更新缓存
                    self._cache[a2a_session_id] = result
                    # 更新最后使用时间
                    self._update_last_used(a2a_session_id)
                    return result
                
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"查询会话映射错误: {e}")
            return None
    
    def save_session(self, a2a_session_id: str, ragflow_session_id: str, agent_type: str, agent_id: str) -> bool:
        """
        保存会话映射
        
        Args:
            a2a_session_id: A2A会话ID
            ragflow_session_id: RagFlow会话ID
            agent_type: 代理类型，'chat'或'agent'
            agent_id: chat_id或agent_id
            
        Returns:
            是否保存成功
        """
        try:
            with self.Session() as session:
                # 检查记录是否已存在
                stmt = select(SessionMapping).where(
                    SessionMapping.a2a_session_id == a2a_session_id
                )
                existing = session.execute(stmt).scalar_one_or_none()
                
                if existing:
                    # 更新现有记录
                    existing.ragflow_session_id = ragflow_session_id
                    existing.agent_type = agent_type
                    existing.agent_id = agent_id
                    existing.last_used_at = datetime.utcnow()
                else:
                    # 创建新记录
                    new_mapping = SessionMapping(
                        a2a_session_id=a2a_session_id,
                        ragflow_session_id=ragflow_session_id,
                        agent_type=agent_type,
                        agent_id=agent_id
                    )
                    session.add(new_mapping)
                
                session.commit()
                
                # 更新缓存
                self._cache[a2a_session_id] = ragflow_session_id
                
                logger.info(f"保存会话映射: A2A会话ID {a2a_session_id} -> RagFlow会话ID {ragflow_session_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"保存会话映射错误: {e}")
            return False
    
    def _update_last_used(self, a2a_session_id: str):
        """更新会话最后使用时间"""
        try:
            with self.Session() as session:
                # 使用SQLAlchemy更新
                stmt = update(SessionMapping).where(
                    SessionMapping.a2a_session_id == a2a_session_id
                ).values(
                    last_used_at=datetime.utcnow()
                )
                session.execute(stmt)
                session.commit()
        except SQLAlchemyError as e:
            logger.error(f"更新会话使用时间错误: {e}")
    
    def delete_session(self, a2a_session_id: str) -> bool:
        """
        删除会话映射
        
        Args:
            a2a_session_id: A2A会话ID
            
        Returns:
            是否删除成功
        """
        try:
            with self.Session() as session:
                # 使用SQLAlchemy删除
                stmt = delete(SessionMapping).where(
                    SessionMapping.a2a_session_id == a2a_session_id
                )
                result = session.execute(stmt)
                session.commit()
                
                # 从缓存中删除
                if a2a_session_id in self._cache:
                    del self._cache[a2a_session_id]
                
                return result.rowcount > 0
                
        except SQLAlchemyError as e:
            logger.error(f"删除会话映射错误: {e}")
            return False
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        获取所有会话映射
        
        Returns:
            会话映射列表
        """
        try:
            with self.Session() as session:
                # 使用SQLAlchemy查询
                stmt = select(
                    SessionMapping.a2a_session_id,
                    SessionMapping.ragflow_session_id,
                    SessionMapping.agent_type,
                    SessionMapping.agent_id,
                    SessionMapping.created_at,
                    SessionMapping.last_used_at
                ).order_by(SessionMapping.last_used_at.desc())
                
                results = []
                for row in session.execute(stmt):
                    results.append({
                        "a2a_session_id": row.a2a_session_id,
                        "ragflow_session_id": row.ragflow_session_id,
                        "agent_type": row.agent_type,
                        "agent_id": row.agent_id,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None
                    })
                
                return results
                
        except SQLAlchemyError as e:
            logger.error(f"获取所有会话映射错误: {e}")
            return []
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        清理旧会话
        
        Args:
            days: 清理多少天前未使用的会话
            
        Returns:
            删除的会话数量
        """
        try:
            # 计算截止时间
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 先获取要删除的会话ID
            with self.Session() as session:
                ids_stmt = select(SessionMapping.a2a_session_id).where(
                    SessionMapping.last_used_at < cutoff_date
                )
                to_delete = [row[0] for row in session.execute(ids_stmt)]
                
                # 删除记录
                if to_delete:
                    delete_stmt = delete(SessionMapping).where(
                        SessionMapping.a2a_session_id.in_(to_delete)
                    )
                    result = session.execute(delete_stmt)
                    session.commit()
                    
                    # 从缓存中删除
                    for a2a_session_id in to_delete:
                        if a2a_session_id in self._cache:
                            del self._cache[a2a_session_id]
                    
                    deleted_count = result.rowcount
                    if deleted_count > 0:
                        logger.info(f"已清理 {deleted_count} 个旧会话")
                    
                    return deleted_count
                
                return 0
                
        except SQLAlchemyError as e:
            logger.error(f"清理旧会话错误: {e}")
            return 0

# 如果直接运行此模块，执行简单测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = SessionManager()
    print(f"使用数据库: {manager.db_url}")
    print("获取所有会话:", manager.get_all_sessions())
    
    # 测试保存会话
    test_id = "test-session-" + str(int(time.time()))
    if manager.save_session(test_id, "ragflow-" + test_id, "chat", "chat123"):
        print(f"保存会话成功: {test_id}")
    
    # 测试获取会话
    retrieved = manager.get_session(test_id)
    print(f"获取会话 {test_id}: {retrieved}")
    
    # 测试删除会话
    if manager.delete_session(test_id):
        print(f"删除会话成功: {test_id}") 