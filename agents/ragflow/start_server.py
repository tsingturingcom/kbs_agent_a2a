#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KBS_Agent_A2A gRhV服务
"""

import sys
import os
import logging
from pathlib import Path
import argparse

# 添加Python模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))  # 上溯两级到项目根目录
sys.path.insert(0, project_root)  # 添加项目根目录到Python路径

# 导入服务模块
from agents.ragflow.__main__ import main as start_server

# 设置日志
def setup_logging():
    # 确保log目录存在
    log_dir = Path('log')
    log_dir.mkdir(exist_ok=True)
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # 控制台输出
            logging.FileHandler('log/kbs_a2a_server.log', encoding='utf-8')  # 文件输出
        ]
    )
    return logging.getLogger('kbs_a2a_server')

def main():
    logger = setup_logging()
    parser = argparse.ArgumentParser(description='KBS Agent A2A 服务')
    
    # 设置命令行参数
    parser.add_argument('--host', default='localhost', help='服务器主机，默认为localhost')
    parser.add_argument('--port', type=int, default=10003, help='服务器端口，默认为10003')
    parser.add_argument('--chat-id', help='会话ID')
    parser.add_argument('--agent-id', help='智能体ID')
    parser.add_argument('--url', help='API URL')
    
    args = parser.parse_args()
    
    # 构建服务地址
    server_address = f"{args.host}:{args.port}"
    
    # 记录启动信息
    logger.info(f"KBS Agent A2A 服务: {server_address}")
    if args.chat_id:
        logger.info(f"会话ID: {args.chat_id}")
    if args.agent_id:
        logger.info(f"智能体ID: {args.agent_id}")
    if args.url:
        logger.info(f"API URL: {args.url}")
    
    # 设置参数
    sys_args = ['--host', args.host, '--port', str(args.port)]
    if args.chat_id:
        sys_args.extend(['--chat-id', args.chat_id])
    if args.agent_id:
        sys_args.extend(['--agent-id', args.agent_id])
    if args.url:
        sys_args.extend(['--url', args.url])
    
    # 保存原始参数并设置新参数
    orig_args = sys.argv
    sys.argv = [sys.argv[0]] + sys_args
    
    try:
        # 启动服务
        logger.info("正在启动服务...")
        start_server()
    except KeyboardInterrupt:
        logger.info("服务已被用户中断")
    except Exception as e:
        logger.error(f"服务启动错误: {e}", exc_info=True)
    finally:
        # 恢复原始参数
        sys.argv = orig_args

if __name__ == "__main__":
    main()