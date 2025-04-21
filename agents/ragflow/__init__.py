#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RagFlow Agent for A2A Protocol
基于RagFlow的A2A协议代理
"""

__version__ = "0.1.0"

from .agent import RagFlowAgent
from .task_manager import RagFlowTaskManager
from .session_manager import SessionManager

__all__ = ["RagFlowAgent", "RagFlowTaskManager", "SessionManager"]