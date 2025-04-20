#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KBS_Agent_A2A 客户端启动脚本（修订版）
"""
import os
import sys
import importlib.util

# 获取当前脚本的绝对路径
current_file = os.path.abspath(__file__)
# 获取项目根目录
project_root = os.path.dirname(current_file)
# 将项目根目录添加到Python路径
sys.path.insert(0, project_root)

# 检查hosts.kbs_cli模块是否可用
try:
    if importlib.util.find_spec("hosts.kbs_cli") is None:
        print("找不到hosts.kbs_cli模块，请确保你在正确的目录中运行此脚本。")
        sys.exit(1)
    
    # 动态导入模块
    from hosts.kbs_cli.__main__ import cli
    
    # 设置默认的服务器URL
    server_url = "http://localhost:10003"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    # 打印调试信息
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"项目根目录: {project_root}")
    print(f"Python路径: {sys.path}")
    print(f"正在连接KBS_Agent_A2A服务器: {server_url}...")
    
    # 启动客户端
    sys.argv = [sys.argv[0], "--ragflow", server_url]
    cli()

except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保你在项目根目录中运行此脚本，并且已经安装了所有依赖。")
    sys.exit(1)
except Exception as e:
    print(f"启动客户端时出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 