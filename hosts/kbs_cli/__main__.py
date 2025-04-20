#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import sys
import os
import json
import uuid
import requests
import time
import traceback
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.progress import Progress

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))  # 只需上溯两级到项目根目录
if project_root not in sys.path:
    sys.path.insert(0, project_root)  # 直接添加项目根目录

from common.types import TaskState

console = Console()

# 创建一个全局会话对象，保持连接
session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

# 全局设置
DEFAULT_TIMEOUT = 120  # 默认超时时间（秒）
MAX_RETRIES = 3        # 最大重试次数

def get_agent_card(base_url, timeout=30):
    """获取代理卡片"""
    url = f"{base_url.rstrip('/')}/.well-known/agent.json"
    
    try:
        console.print(f"[dim]获取代理卡片: {url}[/dim]")
        response = session.get(url, timeout=timeout)
        
        if response.status_code == 200:
            console.print("[green]获取代理卡片成功[/green]")
            return response.json()
        else:
            console.print(f"[bold red]获取代理卡片失败: HTTP {response.status_code}[/bold red]")
            console.print(f"[dim]{response.text[:200]}...[/dim]")
            return None
    except requests.ConnectionError as e:
        console.print(f"[bold red]连接错误: {str(e)}[/bold red]")
        return None
    except requests.Timeout as e:
        console.print(f"[bold red]请求超时: {str(e)}[/bold red]")
        return None
    except requests.RequestException as e:
        console.print(f"[bold red]请求异常: {str(e)}[/bold red]")
        return None

def display_agent_info(agent_card):
    """显示代理信息"""
    if not agent_card:
        console.print("[bold red]无法显示代理信息: 未获取到代理卡片[/bold red]")
        return
    
    console.print(Panel(f"""
[bold cyan]RagFlow代理信息[/bold cyan]

[bold]名称:[/bold] {agent_card.get('name', '未知')}
[bold]描述:[/bold] {agent_card.get('description', '无描述')}
[bold]URL:[/bold] {agent_card.get('url', '未知')}
[bold]版本:[/bold] {agent_card.get('version', '未知')}
    """, expand=False))
    
    # 显示技能
    skills = agent_card.get('skills', [])
    if skills:
        console.print("[bold cyan]技能:[/bold cyan]")
        for skill in skills:
            console.print(f"• {skill.get('name', '未知')}: {skill.get('description', '无描述')}")

def send_rpc_request(base_url, method, params, timeout=DEFAULT_TIMEOUT, retries=MAX_RETRIES):
    """发送JSON-RPC请求到服务器根路径，带重试机制"""
    url = base_url.rstrip('/')
    
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": params
    }
    
    for attempt in range(retries + 1):
        try:
            if attempt > 0:
                console.print(f"[yellow]第{attempt}次重试发送请求...[/yellow]")
            
            console.print(f"[dim]发送请求到: {url}[/dim]")
            console.print(f"[dim]方法: {method}[/dim]")
            
            response = session.post(url, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                console.print("[green]请求成功[/green]")
                return response.json()
            else:
                console.print(f"[bold red]HTTP错误: {response.status_code}[/bold red]")
                console.print(f"[dim]{response.text[:200]}...[/dim]")
        except requests.ConnectionError as e:
            console.print(f"[bold red]连接错误: {str(e)}[/bold red]")
        except requests.Timeout as e:
            console.print(f"[bold red]请求超时: {str(e)}[/bold red]")
        except requests.RequestException as e:
            console.print(f"[bold red]请求异常: {str(e)}[/bold red]")
        
        if attempt < retries:
            wait_time = 2 * (attempt + 1)  # 递增等待时间
            console.print(f"[yellow]等待 {wait_time} 秒后重试...[/yellow]")
            time.sleep(wait_time)
        else:
            console.print("[bold red]达到最大重试次数，请求失败[/bold red]")
    
    return None

def display_response(response, prompt):
    """显示RagFlow响应"""
    if not response:
        console.print("[bold red]无响应内容[/bold red]")
        return
    
    try:
        result = response.get('result', {})
        if not result:
            error = response.get('error', {})
            if error:
                console.print(f"[bold red]错误: [{error.get('code')}] {error.get('message')}[/bold red]")
                # 特别处理内部错误
                if error.get('code') == -32603 and "调用代理时出错" in error.get('message', ''):
                    console.print("[bold yellow]服务器调用远程API时超时，请尝试更简短的问题[/bold yellow]")
                    console.print("[bold yellow]或者联系管理员增加服务器端的超时设置[/bold yellow]")
            else:
                console.print("[bold red]响应中没有结果[/bold red]")
                console.print(f"[dim]{json.dumps(response, ensure_ascii=False, indent=2)}[/dim]")
            return
        
        status = result.get('status', {})
        state = status.get('state', '未知')
        console.print(f"[bold]任务状态:[/bold] {state}")
        
        if state == "completed" and result.get('artifacts'):
            artifacts = result.get('artifacts', [])
            for artifact in artifacts:
                for part in artifact.get('parts', []):
                    if part.get('type') == 'text':
                        console.print(f"[bold cyan]问题:[/bold cyan] {prompt}")
                        console.print(Panel(Markdown(part.get('text', '')), 
                                          title="RagFlow回答", 
                                          border_style="green"))
                    elif part.get('type') == 'data':
                        data = part.get('data', {})
                        references = data.get('references', {})
                        if references and references.get('chunks'):
                            chunks = references.get('chunks', [])
                            console.print("[bold cyan]知识库引用:[/bold cyan]")
                            for i, chunk in enumerate(chunks, 1):
                                console.print(f"[bold]{i}.[/bold] {chunk.get('content', '')[:150]}...")
                                console.print(f"   [dim]来源: {chunk.get('source', '未知')}[/dim]")
        elif status.get('message'):
            message = status.get('message', {})
            if message.get('parts'):
                for part in message.get('parts', []):
                    if part.get('type') == 'text':
                        console.print(Panel(part.get('text', ''), 
                                          title=f"消息 [{state}]", 
                                          border_style="yellow"))
        else:
            console.print("[bold yellow]任务未提供内容[/bold yellow]")
    
    except Exception as e:
        console.print(f"[bold red]处理响应时出错: {str(e)}[/bold red]")
        console.print(f"[dim]{json.dumps(response, ensure_ascii=False, indent=2)}[/dim]")
        console.print(traceback.format_exc())

def check_server_status(ragflow):
    """检查服务器状态"""
    console.print("[bold]检查RagFlow服务器状态...[/bold]")
    agent_card = None
    
    with Progress() as progress:
        task = progress.add_task("[cyan]尝试连接...", total=MAX_RETRIES)
        
        for i in range(MAX_RETRIES):
            progress.update(task, completed=i)
            agent_card = get_agent_card(ragflow, timeout=10)
            if agent_card:
                progress.update(task, completed=MAX_RETRIES)
                break
                
            if i < MAX_RETRIES - 1:
                progress.update(task, description=f"[yellow]重试 ({i+1}/{MAX_RETRIES})...")
                time.sleep(2)
    
    if not agent_card:
        console.print("[bold red]无法连接到RagFlow服务器[/bold red]")
        console.print("[bold red]请确认服务器已启动并且可以访问[/bold red]")
        return False
        
    return agent_card

def run_client(ragflow, session_id, timeout=DEFAULT_TIMEOUT):
    """运行RagFlow客户端 - 基于A2A协议 (同步版)"""
    try:
        console.print(f"[bold]RagFlow客户端[/bold]")
        console.print(f"[bold]连接到:[/bold] {ragflow}")
        
        # 检查服务器状态
        agent_card = check_server_status(ragflow)
        if not agent_card:
            return
        
        # 显示代理信息
        display_agent_info(agent_card)
        
        # 代理URL
        agent_url = agent_card.get('url').rstrip('/')
        console.print(f"[bold]使用代理URL:[/bold] {agent_url}")
        
        # 会话ID
        client_session_id = session_id or str(uuid.uuid4())
        console.print(f"[bold]会话ID:[/bold] {client_session_id}")
        
        # 对话循环
        while True:
            console.print("\n[bold cyan]请输入问题 (:q 退出):[/bold cyan]")
            question = input().strip()
            
            if not question:
                continue
                
            if question.lower() in [":q", "quit", "exit", "q"]:
                console.print("[bold]感谢使用RagFlow客户端，再见![/bold]")
                break
            
            # 创建任务ID
            task_id = str(uuid.uuid4())
            
            # 发送任务请求
            params = {
                "id": task_id,
                "sessionId": client_session_id,
                "message": {
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            }
            
            # 发送请求 - 使用更长的超时时间和自动重试
            console.print("[bold]正在发送问题...[/bold]")
            with console.status("[bold green]等待回答中...[/bold green]"):
                response = send_rpc_request(
                    agent_url, 
                    "tasks/send", 
                    params, 
                    timeout=timeout
                )
            
            # 显示响应
            if response:
                display_response(response, question)
            else:
                console.print("[bold red]无法获取回答[/bold red]")
                console.print("[bold yellow]提示：请尝试更简短的问题，或稍后再试[/bold yellow]")
                console.print("[bold yellow]服务器可能正在处理其他请求，或远程API暂时不可用[/bold yellow]")
    
    except KeyboardInterrupt:
        console.print("\n[bold]已中断，感谢使用RagFlow客户端[/bold]")
    except Exception as e:
        console.print(f"[bold red]客户端错误: {str(e)}[/bold red]")
        console.print(traceback.format_exc())

@click.command()
@click.option("--ragflow", default="http://localhost:10003", help="RagFlow代理服务地址")
@click.option("--session", default=None, help="会话ID，不指定则自动生成")
@click.option("--timeout", default=DEFAULT_TIMEOUT, help="请求超时时间(秒)")
def cli(ragflow, session, timeout):
    """RagFlow知识库客户端 - 基于A2A协议 (高容错版)"""
    try:
        run_client(ragflow, session, timeout)
    except KeyboardInterrupt:
        console.print("\n[bold]已中断RagFlow客户端[/bold]")
    except Exception as e:
        console.print(f"[bold red]出错了: {str(e)}[/bold red]")
        console.print(traceback.format_exc())

if __name__ == "__main__":
    cli() 