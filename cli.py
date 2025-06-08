#!/usr/bin/env python3
"""
Decepticon CLI - Dynamic Configuration Only
A command-line interface for penetration testing workflows with NO hardcoded values
"""

import asyncio
import uuid
import sys
import os
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Set

# Rich imports for beautiful CLI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich import box
from rich.status import Status
from rich.tree import Tree
from rich.console import Group
from rich.syntax import Syntax
from rich.markdown import Markdown

# Decepticon imports
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.utils.llm.models import (
    list_available_models, 
    check_ollama_connection,
    validate_api_key
)
from src.graphs.swarm import create_dynamic_swarm  # 동적 swarm 생성 함수 import
from src.utils.llm.config_manager import (
    update_llm_config, 
    get_current_llm_config,
    get_current_llm
)
from src.utils.message import (
    extract_message_content,
    get_message_type,
    get_agent_name,
    parse_tool_name
)


from dotenv import load_dotenv
load_dotenv()

console = Console()

class DecepticonCLI:
    def __init__(self):
        self.console = Console()
        self.thread_id = None
        self.config = None
        self.conversation_history = []
        self.strat_time = None
        self.end_time = None
        
        # 메모리에서 관리하는 모델 설정
        self.current_model = None  # 메모리에서 관리
        self.current_llm = None    # 실제 LLM 인스턴스
        self.swarm = None          # 동적으로 생성될 swarm 객체
        
        # 동적으로 로드될 설정들
        self.agents_config = {}
        self.tools_config = {}
        
        # 초기화 시 설정 로드
        self._load_dynamic_config()
    
    def _load_dynamic_config(self):
        """실제 설정 파일에서 동적으로 설정 로드"""
        try:
            # MCP 설정에서 에이전트 정보 로드
            self._load_agents_from_mcp_config()
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not load dynamic config: {str(e)}[/yellow]")
            self.agents_config = {}
    
    def _load_agents_from_mcp_config(self):
        """MCP 설정에서 실제 에이전트 목록 로드"""
        try:
            with open("mcp_config.json", "r") as f:
                mcp_config = json.load(f)
            
            # MCP 설정에서 에이전트 목록 추출
            for agent_name, servers in mcp_config.items():
                self.agents_config[agent_name] = {
                    "servers": servers,
                    "tools": []
                }
                
        except FileNotFoundError:
            self.agents_config = {}
    
    def get_agent_color_cli(self, agent_name):
        """CLI에서 에이전트별 색상 반환"""
        if isinstance(agent_name, str):
            agent_name = agent_name.lower()
            if "planner" in agent_name:
                return "cyan"
            elif "reconnaissance" in agent_name:
                return "magenta"
            elif "initial_access" in agent_name:
                return "yellow"
            elif "execution" in agent_name:
                return "red"
            elif "persistence" in agent_name:
                return "bright_magenta"
            elif "privilege_escalation" in agent_name:
                return "bright_red"
            elif "defense_evasion" in agent_name:
                return "bright_cyan"
            elif "summary" in agent_name:
                return "bright_yellow"
            elif "tool" in agent_name:
                return "green"
        return "blue"  # 기본 색상
    
    def display_banner(self):
        """Decepticon 배너 표시"""
        banner_text = """
██████╗ ███████╗ ██████╗███████╗██████╗ ████████╗██╗ ██████╗ ██████╗ ███╗   ██║
██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝██╔═══██╗████╗  ██║
██║  ██║█████╗  ██║     █████╗  ██████╔╝   ██║   ██║██║     ██║   ██║██╔██╗ ██║
██║  ██║██╔══╝  ██║     ██╔══╝  ██╔═══╝    ██║   ██║██║     ██║   ██║██║╚██╗██║
██████╔╝███████╗╚██████╗███████╗██║        ██║   ██║╚██████╗╚██████╔╝██║ ╚████║
╚═════╝ ╚══════╝ ╚═════╝╚══════╝╚═╝        ╚═╝   ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   
        """
        
        banner_panel = Panel(
            Align.center(
                Text(banner_text, style="bold red")
            ),
            box=box.DOUBLE,
            border_style="red",
            title="[bold red] DECEPTICON [/bold red]",
            title_align="center",
            subtitle="[bold cyan] Vibe Hacking Agent [/bold cyan]",
            subtitle_align="center"
        )
        
        
        # 시스템 정보와 환영 메시지
        info_lines = [
            "[bold magenta]🚀 System Status[/bold magenta]",
            f"├── 🕒 Time: [green]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/green]",
            f"├── 🐍 Python: [yellow]{sys.version.split()[0]}[/yellow]",
            f"├── 💻 Platform: [blue]{sys.platform.upper()}[/blue]",
            "└── 🎯 Mode: [bold magenta]Interactive CLI[/bold magenta]"
        ]
        
        welcome_lines = [
            "[bold magenta]🎮 Available Commands[/bold magenta]",
            "",
            "[green]• help[/green] - Show detailed help guide",
            "[green]• llm[/green] - Show current LLM configuration", 
            "[green]• model-change[/green] - Change LLM model",
            "[green]• mcp-info[/green] - Show MCP tools information",
            "[green]• clear[/green] - Clear the screen",
            "[green]• quit/exit[/green] - Exit the program",
            "",
            "[cyan]💡 Just type your security requests![/cyan]",
            "[dim]Example: 'Scan 192.168.1.1 with nmap'[/dim]"
        ]

        info_panel = Panel("\n".join(info_lines), box=box.ROUNDED, border_style="cyan", title="[bold cyan]System Information[/bold cyan]", width=60)
        welcome_panel = Panel("\n".join(welcome_lines), box=box.ROUNDED, border_style="green", title="[bold green]Quick Commands[/bold green]", width=60)


        self.console.print()
        self.console.print(banner_panel)
        self.console.print()
        
        columns = Columns([info_panel, welcome_panel], equal=True, expand=True)
        self.console.print(columns)
        self.console.print()
    


    async def display_mcp_infrastructure(self):
        """MCP 인프라 정보 표시 (load_mcp_tools를 직접 구현)"""
        try:
            self.console.print(Panel(
                "[bold yellow]🚀 Initializing MCP Server[/bold yellow]\n\n"
                "[cyan]Loading MCP tool information...[/cyan]",
                box=box.ROUNDED,
                border_style="yellow",
                title="[bold yellow]🛠️ MCP Server[/bold yellow]"
            ))

            self.tools_config = {}  # 초기화
            root = Tree("[bold cyan]📦 MCP Agents & Tools[/bold cyan]", guide_style="bold bright_blue")

            for agent_name, agent_info in self.agents_config.items():
                agent_node = root.add(f"[bold green]🧠 Agent:[/bold green] {agent_name}")

                if not agent_info.get("servers"):
                    agent_node.add("[dim italic]⚠️  No MCP servers configured[/dim italic]")
                    continue

                for server_name, server_config in agent_info["servers"].items():
                    if "transport" not in server_config:
                        server_config["transport"] = "streamable_http" if "url" in server_config else "stdio"

                    client = MultiServerMCPClient({server_name: server_config})
                    tools = await client.get_tools() if client else []

                    server_node = agent_node.add(f"[bold yellow]🖥️  Server:[/bold yellow] {server_name}")
                    if "url" in server_config:
                        server_node.add(f"[dim]🌐  URL: {server_config['url']}[/dim]")

                    if tools:
                        tools_node = server_node.add("[bold magenta]🧰  Tools[/bold magenta]")
                        for tool in tools:
                            display_name = tool.name.replace("_", " ").title()
                            tools_node.add(f"[white]• {display_name}[/white]")
                            self.tools_config[tool.name] = {
                                "display_name": display_name,
                                "server": server_name,
                                "agent": agent_name,
                            }
                    else:
                        server_node.add("[yellow]⚠️ No tools available (MCP server might be offline)[/yellow]")

            self.console.print(Panel(
                Group(root),
                box=box.ROUNDED,
                border_style="cyan",
                title="[bold cyan]📊 MCP Overview[/bold cyan]"
            ))

        except Exception as e:
            self.console.print(Panel(
                f"[red]❌ MCP Infrastructure Error[/red]\n\n"
                f"[yellow]Error:[/yellow] {str(e)}\n"
                f"[dim]Continuing with available functionality[/dim]",
                box=box.ROUNDED,
                border_style="red",
                title="[bold red]⚠️ MCP Error[/bold red]"
            ))

    
    def display_model_selection(self):
        """LLM 모델 선택 화면"""
        self.console.print(Panel(
            "[bold yellow]🤖 LLM Model Selection[/bold yellow]\n\n"
            "[dim]Choose your AI model for red team operations[/dim]",
            box=box.ROUNDED,
            border_style="yellow"
        ))
        
        with Status("[bold green]Loading available models...", console=self.console) as status:
            try:
                models = list_available_models()
                ollama_info = check_ollama_connection()
                status.update("[bold green]Models loaded successfully!")
                time.sleep(0.5)
                
            except Exception as e:
                status.update(f"[bold red]Error loading models: {str(e)}")
                self.console.print(f"[red]❌ Error loading models: {str(e)}[/red]")
                return None
        
        # 사용 가능한 모델만 필터링
        available_models = [m for m in models if m["api_key_available"]]
        
        if not available_models:
            self.console.print(Panel(
                "[red]❌ No models available[/red]\n\n"
                "[yellow]Setup required:[/yellow]\n"
                "• Set API keys in .env file (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)\n"
                "• Or install Ollama from https://ollama.ai/",
                box=box.ROUNDED,
                border_style="red",
                title="Setup Required"
            ))
            return None
        
        # 모델 테이블 생성
        table = Table(
            title="🤖 Available LLM Models",
            box=box.ROUNDED,
            header_style="bold magenta",
            show_lines=True,
            title_style="bold cyan"
        )
        
        table.add_column("ID", style="bold cyan", width=4, justify="center")
        table.add_column("Model Name", style="bold green", width=35)
        table.add_column("Provider", style="bold blue", width=12)
        table.add_column("Status", style="yellow", width=10, justify="center")
        
        # 사용 가능한 모델들을 테이블에 추가
        for i, model in enumerate(available_models, 1):
            status_icon = "✅" if model["api_key_available"] else "❌"
            
            table.add_row(
                f"[bold cyan]{i}[/bold cyan]",
                f"[bold]{model['display_name']}[/bold]",
                f"[bold]{model['provider']}[/bold]",
                status_icon
            )
        
        self.console.print(table)
        
        # Ollama 상태 표시
        if ollama_info["connected"]:
            ollama_panel = Panel(
                f"[green]🟢 Ollama: Running[/green] ({ollama_info['count']} models available)\n"
                f"[cyan]Models:[/cyan] {', '.join(ollama_info['models'][:3])}{'...' if len(ollama_info['models']) > 3 else ''}",
                box=box.ROUNDED,
                border_style="green",
                title="🦙 Ollama Local Models"
            )
            self.console.print(ollama_panel)
        
        # 사용자 선택
        self.console.print()
        while True:
            try:
                choice = Prompt.ask(
                    "[bold cyan]Select model by ID[/bold cyan] [dim](or 'q' to quit)[/dim]",
                    choices=[str(i) for i in range(1, len(available_models) + 1)] + ["q"],
                    default="1"
                )
                
                if choice.lower() == 'q':
                    return None
                
                selected_idx = int(choice) - 1
                selected_model = available_models[selected_idx]
                
                # 선택 확인
                confirm_panel = Panel(
                    f"[bold green]Selected Model:[/bold green]\n"
                    f"[cyan]• Name:[/cyan] {selected_model['display_name']}\n"
                    f"[cyan]• Provider:[/cyan] {selected_model['provider']}\n"
                    f"[cyan]• Model:[/cyan] {selected_model['model_name']}",
                    box=box.ROUNDED,
                    border_style="green",
                    title="Model Confirmation"
                )
                self.console.print(confirm_panel)
                
                if Confirm.ask("[green]Confirm this selection?[/green]", default=True):
                    return selected_model
                
            except (ValueError, IndexError):
                self.console.print("[red]❌ Invalid selection. Please try again.[/red]")
    
    async def setup_session(self, model_info: Dict[str, Any]):
        """세션 설정 - 메모리에서 모델 관리 및 동적 swarm 생성"""
        with Status("[bold green]Setting up session...", console=self.console) as status:
            try:
                # 쓰레드 ID 생성
                self.thread_id = str(uuid.uuid4())
                
                # 설정 초기화
                self.config = {
                    "configurable": {
                        "thread_id": self.thread_id,
                    }
                }
                
                # 메모리에서 모델 정보 저장
                self.current_model = model_info
                
                # 메모리 기반 전역 설정 업데이트 (파일 저장하지 않음)
                status.update("[bold green]Updating memory configuration...")
                update_llm_config(
                    model_name=model_info['model_name'],
                    provider=model_info['provider'],
                    display_name=model_info['display_name'],
                    temperature=0.0  # 고정값
                )
                
                # LLM 인스턴스 생성
                status.update("[bold green]Loading LLM instance...")
                self.current_llm = get_current_llm()
                
                status.update("[bold green]Memory configuration updated!")
                time.sleep(0.5)
                
                # 동적으로 swarm 생성 (모델 선택 후)
                status.update("[bold green]Creating AI agents with selected model...")
                self.swarm = await create_dynamic_swarm()
                
                status.update("[bold green]Session setup complete!")
                time.sleep(1)
                
            except Exception as e:
                status.update(f"[bold red]Setup failed: {str(e)}")
                raise
        
        # 세션 정보 표시
        session_panel = Panel(
            f"[bold green]✅ Session Ready[/bold green]\n\n"
            f"[cyan]🤖 Model:[/cyan] [bold]{self.current_model['display_name']}[/bold]\n"
            f"[cyan]🏢 Provider:[/cyan] [bold]{self.current_model['provider']}[/bold]\n"
            f"[cyan]🆔 Thread:[/cyan] [dim]{self.thread_id[:8]}...[/dim]\n"
            f"[cyan]🕒 Started:[/cyan] [bold]{datetime.now().strftime('%H:%M:%S')}[/bold]\n"
            f"[cyan]🤖 Agents:[/cyan] [bold]Dynamically created with selected model[/bold]\n\n"
            f"[yellow]🎯 Ready for red team operations![/yellow]\n"
            f"[dim]All AI agents will use the selected model (memory-based)[/dim]",
            box=box.ROUNDED,
            border_style="green",
            title="[bold green]🚀 Session Initialized[/bold green]"
        )
        
        self.console.print(session_panel)
    
    def display_current_llm_config(self):
        """현재 LLM 설정 표시"""
        try:
            current_config = get_current_llm_config()
            
            config_panel = Panel(
                f"[bold cyan]🤖 Current LLM Configuration[/bold cyan]\n\n"
                f"[cyan]Model:[/cyan] [bold]{current_config.display_name}[/bold]\n"
                f"[cyan]Provider:[/cyan] [bold]{current_config.provider}[/bold]\n"
                f"[cyan]Model Name:[/cyan] [white]{current_config.model_name}[/white]\n"
                f"[cyan]Temperature:[/cyan] [white]0 (fixed)[/white]\n\n"
                f"[green]✅ This model is used by all AI agents[/green]",
                box=box.ROUNDED,
                border_style="cyan",
                title="[bold cyan]🔧 LLM Configuration[/bold cyan]"
            )
            
            self.console.print(config_panel)
            
        except Exception as e:
            self.console.print(Panel(
                f"[red]❌ Error displaying LLM configuration[/red]\n\n"
                f"[yellow]Error:[/yellow] {str(e)}",
                box=box.ROUNDED,
                border_style="red",
                title="Configuration Error"
            ))
    
    async def display_mcp_tools_info(self):
        """MCP 도구 정보 표시"""
        try:
            self.console.print("\n[bold cyan]🔧 MCP Tools Information[/bold cyan]\n")
            
            # 실제 로드된 도구들 표시
            root = Tree("[bold cyan]MCP Agents & Tools[/bold cyan]")
            
            for agent_name, agent_info in self.agents_config.items():
                agent_node = root.add(f"[bold green]Agent:[/bold green] {agent_name}")
                
                if not agent_info.get("servers"):
                    agent_node.add("[red]No MCP servers configured[/red]")
                    continue
                
                for server_name, server_config in agent_info["servers"].items():
                    server_node = agent_node.add(f"[bold yellow]Server:[/bold yellow] {server_name}")
                    
                    # 서버 URL 표시
                    if "url" in server_config:
                        server_node.add(f"[dim]URL: {server_config['url']}[/dim]")
                    
                    # 실제 도구 목록 표시
                    if self.tools_config:
                        tools_node = server_node.add("[bold magenta]Available Tools[/bold magenta]")
                        for tool_name, tool_info in self.tools_config.items():
                            tools_node.add(f"[white]  {tool_info['display_name']}[/white]")
                    else:
                        server_node.add("[yellow]No tools loaded yet[/yellow]")
            
            self.console.print(root)
                
        except Exception as e:
            self.console.print(Panel(
                f"[red]❌ Error displaying MCP tools info[/red]\n\n"
                f"[yellow]Error:[/yellow] {str(e)}",
                box=box.ROUNDED,
                border_style="red",
                title="MCP Tools Error"
            ))
            
    async def change_model(self):
        """세션 도중 모델 변경"""
        self.console.print(Panel(
            "[bold yellow]🔄 Model Change[/bold yellow]\n\n"
            "[dim]Change your AI model during the session[/dim]",
            box=box.ROUNDED,
            border_style="yellow",
            title="[bold yellow]🤖 Change LLM Model[/bold yellow]"
        ))
        
        # 현재 모델 정보 표시
        if self.current_model:
            current_panel = Panel(
                f"[cyan]Current Model:[/cyan] [bold]{self.current_model['display_name']}[/bold]\n"
                f"[cyan]Provider:[/cyan] [bold]{self.current_model['provider']}[/bold]",
                box=box.ROUNDED,
                border_style="blue",
                title="[bold blue]📊 Current Model[/bold blue]"
            )
            self.console.print(current_panel)
        
        # 새로운 모델 선택
        new_model_info = self.display_model_selection()
        if not new_model_info:
            self.console.print("[yellow]⚠️ Model change cancelled[/yellow]")
            return False
        
        # 모델 변경 확인
        if (self.current_model and 
            new_model_info['model_name'] == self.current_model['model_name'] and 
            new_model_info['provider'] == self.current_model['provider']):
            self.console.print(Panel(
                "[yellow]⚠️ Same model selected[/yellow]\n\n"
                "[dim]No changes made[/dim]",
                box=box.ROUNDED,
                border_style="yellow",
                title="No Change"
            ))
            return False
        
        # 모델 변경 진행
        old_model_name = self.current_model['display_name'] if self.current_model else "Previous Model"
        
        with Status("[bold green]Changing model and recreating agents...", console=self.console) as status:
            try:
                # 메모리 설정 업데이트
                status.update("[bold green]Updating model configuration...")
                self.current_model = new_model_info
                
                update_llm_config(
                    model_name=new_model_info['model_name'],
                    provider=new_model_info['provider'],
                    display_name=new_model_info['display_name'],
                    temperature=0.0
                )
                
                # 새로운 LLM 인스턴스 생성
                status.update("[bold green]Loading new LLM instance...")
                self.current_llm = get_current_llm()
                
                # 새로운 모델로 에이전트들 재생성
                status.update("[bold green]Recreating AI agents with new model...")
                self.swarm = await create_dynamic_swarm()
                
                status.update("[bold green]Model change completed!")
                time.sleep(1)
                
            except Exception as e:
                status.update(f"[bold red]Model change failed: {str(e)}")
                self.console.print(Panel(
                    f"[bold red]❌ Model Change Failed[/bold red]\n\n"
                    f"[yellow]Error:[/yellow] {str(e)}\n"
                    f"[dim]Keeping previous model[/dim]",
                    box=box.ROUNDED,
                    border_style="red",
                    title="[bold red]⚠️ Error[/bold red]"
                ))
                return False
        
        # 성공 메시지
        success_panel = Panel(
            f"[bold green]✅ Model Changed Successfully[/bold green]\n\n"
            f"[cyan]🆕 From:[/cyan] [dim]{old_model_name}[/dim]\n"
            f"[cyan]🆕 To:[/cyan] [bold]{new_model_info['display_name']}[/bold]\n"
            f"[cyan]🏢 Provider:[/cyan] [bold]{new_model_info['provider']}[/bold]\n\n"
            f"[yellow]🚀 All agents updated with new model![/yellow]",
            box=box.ROUNDED,
            border_style="green",
            title="[bold green]🎉 Model Updated[/bold green]"
        )
        self.console.print(success_panel)
        
        return True
            
    def display_help(self):
        """도움말 표시"""
        help_content = """
    [bold cyan]📖 Decepticon CLI Help Guide[/bold cyan]

    [yellow]🎯 How to Use:[/yellow]
    Type your penetration testing requests in natural language.
    The AI agents will coordinate to execute your commands.

    [yellow]💡 Example Requests:[/yellow]
    • [green]"Scan 192.168.1.1 with nmap"[/green]
    • [green]"Perform reconnaissance on example.com"[/green]  
    • [green]"Test SSH login with default credentials"[/green]
    • [green]"Check for web vulnerabilities"[/green]

    [yellow]🎮 Special Commands:[/yellow]
    • [green]help[/green] - Show this help guide
    • [green]llm[/green] - Show current LLM configuration
    • [green]model-change[/green] - Change LLM model during session
    • [green]mcp-info[/green] - Show MCP tools information
    • [green]clear[/green] - Clear the screen
    • [green]quit/exit[/green] - Exit the program

    [yellow]🤖 AI Agents:[/yellow]
    Dynamic agents loaded from MCP configuration
        """
        
        help_panel = Panel(
            help_content,
            box=box.ROUNDED,
            border_style="cyan",
            title="[bold cyan]📚 Help & Usage Guide[/bold cyan]"
        )
        
        self.console.print(help_panel)
    
    def should_display_message(self, message, agent_name, step_count):
            """메시지를 표시할지 결정 - 중복 방지"""
            # processed_message_ids 초기화 (없으면 생성)
            if not hasattr(self, 'processed_message_ids'):
                self.processed_message_ids = set()
                
            # 메시지 ID 생성
            message_id = None
            if hasattr(message, 'id') and message.id:
                message_id = message.id
            else:
                content = extract_message_content(message)
                message_id = f"{agent_name}_{hash(content)}"
            
            # 사용자 메시지는 최초 1회만 표시
            if message.__class__.__name__ == 'HumanMessage':
                if message_id not in self.processed_message_ids:
                    self.processed_message_ids.add(message_id)
                    return True, "user"
                return False, None
            
            # AI 메시지는 새로운 것만 표시
            elif message.__class__.__name__ == 'AIMessage':
                if message_id not in self.processed_message_ids:
                    self.processed_message_ids.add(message_id)
                    return True, "ai"
                return False, None
            
            # 도구 메시지는 항상 표시
            elif message.__class__.__name__ == 'ToolMessage':
                if message_id not in self.processed_message_ids:
                    self.processed_message_ids.add(message_id)
                    return True, "tool" 
                return False, None
            
            return False, None



    async def execute_workflow(self, user_input: str):
        """워크플로우 실행"""
        # Swarm이 아직 생성되지 않았는지 확인
        if not self.swarm:
            error_panel = Panel(
                f"[bold red]❌ Swarm not initialized[/bold red]\n\n"
                f"[yellow]에이전트가 아직 초기화되지 않았습니다.[/yellow]\n"
                f"[dim]세션을 다시 시작해주세요.[/dim]",
                box=box.ROUNDED,
                border_style="red",
                title="[bold red]⚠️ Initialization Error[/bold red]"
            )
            self.console.print(error_panel)
            return False
            
        self.conversation_history.append(("user", user_input))
        
        # 메시지 ID 추적 초기화 (새로운 워크플로우 시작)
        self.processed_message_ids = set()
        
        inputs = {"messages": [HumanMessage(content=user_input)]}
        
        # 워크플로우 실행
        agent_responses = {}
        step_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            main_task = progress.add_task("[bold green]🤖 Working...", total=None)

            try:
                async for namespace, output in self.swarm.astream(
                    inputs,
                    stream_mode="updates",
                    config=self.config,
                    subgraphs=True
                ):
                    step_count += 1

                    for node, value in output.items():
                        # 에이전트 이름 결정
                        agent_name = get_agent_name(namespace)
            
                        
                        # 메시지 처리
                        if "messages" in value and value["messages"]:
                            messages = value["messages"]
                            if messages:
                                latest_message = messages[-1]
                                should_display, message_type = self.should_display_message(latest_message, agent_name, step_count)
                                
                                if should_display:
                                    progress.stop()

                                    if message_type == "ai":
                                        content = extract_message_content(latest_message)

                                        try:
                                            # 에이전트별 색상 설정
                                            agent_color = self.get_agent_color_cli(agent_name)
                                            content = Markdown(content)
                                            
                                            agent_panel = Panel(
                                                content,
                                                box=box.ROUNDED,
                                                border_style=agent_color,
                                                title=f"[{agent_color} bold]{agent_name}[/{agent_color} bold]"
                                            )
                                            self.console.print(agent_panel)
                                        except Exception as panel_error:
                                            # Panel 출력 실패 시 기본 출력
                                            self.console.print(f"[{agent_name}]: {content}")

                                        if agent_name not in agent_responses:
                                            agent_responses[agent_name] = []
                                        agent_responses[agent_name].append(content)

                                    elif message_type == "tool":
                                        content = extract_message_content(latest_message)
                                        tool_name = getattr(latest_message, 'name', 'Unknown Tool')
                                        tool_display_name = parse_tool_name(tool_name)

                                        try:
                                            # 도구는 녹색으로 고정
                                            tool_color = "green"
                                            
                                            tool_panel = Panel(
                                                content,
                                                box=box.ROUNDED,
                                                border_style=tool_color,
                                                title=f"[bold {tool_color}]{tool_display_name}[/bold {tool_color}]"
                                            )
                                            self.console.print(tool_panel)
                                        except Exception as panel_error:
                                            # Panel 출력 실패 시 기본 출력
                                            self.console.print(f"[{tool_display_name}]: {content}")

                                # 진행 상황 재시작
                                progress.start()
                                progress.update(main_task, description=f"[bold blue]🤖 Working... [/bold blue]")

                # 워크플로우 완료 후 완료 상태 표시
                progress.update(main_task, description="[bold green]✅ Workflow completed!")
                time.sleep(1)
                progress.stop()

                # 완료 요약
                completion_panel = Panel(
                    f"[bold green]✅ Operation Completed[/bold green]\n\n"
                    f"[cyan]📊 Agents:[/cyan] {', '.join(agent_responses.keys())}\n"
                    f"[cyan]📝 Responses:[/cyan] {sum(len(responses) for responses in agent_responses.values())}\n"
                    f"[cyan]🔄 Steps:[/cyan] {step_count}\n"
                    f"[cyan]🕒 Time:[/cyan] {datetime.now().strftime('%H:%M:%S')}",
                    box=box.ROUNDED,
                    border_style="green",
                    title="[bold green]🎉 Success[/bold green]"
                )
                self.console.print(completion_panel)

                return True

            except Exception as e:
                progress.update(main_task, description=f"[bold red]❌ Error: {str(e)}")
                time.sleep(2)
                progress.stop()

                error_panel = Panel(
                    f"[bold red]❌ Workflow Error[/bold red]\n\n"
                    f"[yellow]Error:[/yellow] {str(e)}\n"
                    f"[dim]Please try again[/dim]",
                    box=box.ROUNDED,
                    border_style="red",
                    title="[bold red]⚠️ Error[/bold red]"
                )
                self.console.print(error_panel)
                return False

    
    async def interactive_session(self):
        """대화형 세션"""
        start_panel = Panel(
            f"[bold green]🚀 Interactive Session Started[/bold green]\n\n"
            f"[cyan]🎯 Ready for red team operations[/cyan]\n"
            f"[cyan]💡 Type your requests in natural language[/cyan]\n"
            f"[cyan]❓ Use 'help' for guidance[/cyan]\n\n"
            f"[yellow]Model:[/yellow] [bold]{self.current_model['display_name']}[/bold]",
            box=box.ROUNDED,
            border_style="green",
            title="[bold green]🎮 Interactive Mode[/bold green]"
        )
        
        self.console.print(start_panel)
        
        while True:
            try:
                user_input = Prompt.ask(
                    prompt="\n[bold red] Decepticon > [/bold red]",
                    show_default=False,
                ).strip()
                
                if not user_input:
                    continue
                
                # 특수 명령어 처리
                if user_input.lower() in ['quit', 'exit', 'q']:
                    if Confirm.ask("\n[yellow]Exit Decepticon?[/yellow]"):
                        break
                elif user_input.lower() == 'help':
                    self.display_help()
                elif user_input.lower() == 'llm':
                    self.display_current_llm_config()
                elif user_input.lower() in ['model-change', 'change-model']:
                    await self.change_model()
                elif user_input.lower() == 'mcp-info':
                    await self.display_mcp_tools_info()
                elif user_input.lower() == 'clear':
                    self.console.clear()
                    self.display_banner()
                else:
                    # 워크플로우 실행
                    await self.execute_workflow(user_input)
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]⚠️ Interrupted by user[/yellow]")
                if Confirm.ask("[yellow]Exit Decepticon?[/yellow]"):
                    break
            except Exception as e:
                error_panel = Panel(
                    f"[bold red]❌ Session Error[/bold red]\n\n"
                    f"[yellow]Error:[/yellow] {str(e)}",
                    box=box.ROUNDED,
                    border_style="red",
                    title="Error"
                )
                self.console.print(error_panel)
        
        # 종료 메시지
        farewell_panel = Panel(
            "[bold cyan]👋 Thank you for using Decepticon![/bold cyan]\n\n"
            "[green]🛡️ Stay secure and happy hacking![/green]",
            box=box.ROUNDED,
            border_style="cyan",
            title="[bold cyan]🎉 Session Complete[/bold cyan]"
        )
        self.console.print(farewell_panel)
    
    async def run(self):
        """메인 실행 함수"""
        try:
            # 1. 배너 표시
            self.display_banner()
            
            # 2. MCP 인프라 정보 표시
            await self.display_mcp_infrastructure()
            
            # 3. LLM 모델 선택
            model_info = self.display_model_selection()
            if not model_info:
                self.console.print(Panel(
                    "[red]❌ No model selected[/red]\n\n"
                    "[yellow]Decepticon requires an AI model to function.[/yellow]",
                    box=box.ROUNDED,
                    border_style="red",
                    title="Startup Failed"
                ))
                return
            
            # 4. 세션 설정
            await self.setup_session(model_info)
            
            # 5. 대화형 세션 시작
            await self.interactive_session()
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️ Program interrupted[/yellow]")
        except Exception as e:
            error_panel = Panel(
                f"[bold red]❌ Fatal Error[/bold red]\n\n"
                f"[yellow]Error:[/yellow] {str(e)}",
                box=box.ROUNDED,
                border_style="red",
                title="Fatal Error"
            )
            self.console.print(error_panel)


async def main():
    """메인 엔트리 포인트"""
    try:
        cli = DecepticonCLI()
        await cli.run()
    except ImportError as e:
        console.print(Panel(
            f"[bold red]❌ Import Error[/bold red]\n\n"
            f"[yellow]Missing dependency:[/yellow] {str(e)}\n\n"
            f"[cyan]Solutions:[/cyan]\n"
            f"• Run from project root directory\n"
            f"• Install dependencies: [green]pip install -e .[/green]",
            box=box.ROUNDED,
            border_style="red",
            title="Setup Error"
        ))
    except Exception as e:
        console.print(Panel(
            f"[bold red]❌ Startup Error[/bold red]\n\n"
            f"[yellow]Error:[/yellow] {str(e)}",
            box=box.ROUNDED,
            border_style="red",
            title="Startup Failed"
        ))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold cyan]👋 Goodbye![/bold cyan]")
    except Exception as e:
        try:
            # 안전한 에러 출력
            from rich import markup
            error_msg = markup.escape(str(e))
            console.print(f"[bold red]❌ Critical Error: {error_msg}[/bold red]")
        except:
            # Rich도 실패하면 기본 print 사용
            print(f"Critical Error: {str(e)}")