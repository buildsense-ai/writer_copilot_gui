#!/usr/bin/env python3
"""Interactive CLI chat interface."""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from dotenv import load_dotenv

from src.infra import setup_infrastructure, get_project_id
from src.infrastructure.database.connection import init_database
from src.core.agent.memory_driven_agent import MemoryDrivenAgent
from src.core.skills.skill_service import SkillService
from src.skills.initialize import initialize_all_tools

# Load environment variables
load_dotenv()

console = Console()


class ChatInterface:
    """Interactive chat interface."""

    def __init__(self):
        self.session_id = None
        self.message_count = 0
        self.prompt_session = PromptSession()

    def print_welcome(self):
        """Print welcome message."""
        console.print("\n")
        console.print("[bold cyan]CLI Agent - 智能助手[/bold cyan]")
        console.print("[dim]输入 /help 查看命令，/exit 退出[/dim]")
        console.print("[dim]" + "─" * 60 + "[/dim]\n")

    def print_help(self):
        """Print help message."""
        console.print("\n可用命令：")
        console.print("  /help    - 显示此帮助信息")
        console.print("  /clear   - 清除对话历史")
        console.print("  /exit    - 退出聊天\n")

    def print_stats(self):
        """Print session statistics."""
        console.print(f"\n会话 ID: {self.session_id[:8]}..." if self.session_id else "会话未创建")
        console.print(f"消息数量: {self.message_count}\n")

    def process_command(self, command: str) -> bool:
        """
        Process special commands.
        
        Returns:
            True if should continue, False if should exit
        """
        if command == "/help":
            self.print_help()
            return True
        elif command == "/clear":
            self.session_id = None
            self.message_count = 0
            console.print("\n✓ 对话历史已清除\n")
            return True
        elif command == "/stats":
            self.print_stats()
            return True
        elif command == "/exit":
            console.print("\n[yellow]再见！[/yellow]\n")
            return False
        else:
            console.print(f"\n未知命令: {command}")
            console.print("输入 /help 查看可用命令\n")
            return True

    def chat_loop(self):
        """Main chat loop."""
        # Check API key
        if not os.getenv("OPENROUTER_API_KEY"):
            console.print("[red]Error: OPENROUTER_API_KEY not found in environment.[/red]")
            console.print("[yellow]Please set your OpenRouter API key in .env file[/yellow]")
            return

        self.print_welcome()

        # Initialize
        project_id = setup_infrastructure()
        init_database()
        initialize_all_tools()

        # Index skills
        skill_service = SkillService(project_id)
        skill_service.index_skills()
        console.print("[green]Skills indexed successfully[/green]\n")

        # Create agent
        agent = MemoryDrivenAgent(project_id)

        while True:
            try:
                user_input = self.prompt_session.prompt(
                    HTML('<ansibrightcyan><b>你:</b></ansibrightcyan> ')
                ).strip()

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    should_continue = self.process_command(user_input)
                    if not should_continue:
                        break
                    continue

                # Process message
                console.print()
                
                response = agent.process_message(user_input, self.session_id)

                if not self.session_id:
                    self.session_id = response.get("session_id")

                if response.get("success"):
                    console.print(f"[cyan]助手:[/cyan] {response['text']}\n")
                    self.message_count += 1
                else:
                    console.print(f"[red]错误:[/red] {response.get('error', '未知错误')}\n")

            except (EOFError, KeyboardInterrupt):
                console.print("\n\n[yellow]再见！[/yellow]\n")
                break
            except Exception as e:
                console.print(f"\n[red]发生错误:[/red] {str(e)}\n")
                import traceback
                traceback.print_exc()


def main():
    """Main entry point."""
    chat = ChatInterface()
    chat.chat_loop()


if __name__ == "__main__":
    main()
