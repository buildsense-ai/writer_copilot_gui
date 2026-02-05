#!/usr/bin/env python3
"""Test script for basic functionality."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from rich.console import Console

from src.infra import setup_infrastructure
from src.core.agent.memory_driven_agent import MemoryDrivenAgent
from src.skills.initialize import initialize_all_tools

load_dotenv()
console = Console()


def test_basic_functionality():
    """Test basic agent functionality."""
    console.print("[cyan]Testing CLI Agent...[/cyan]\n")
    
    # Initialize
    project_id = setup_infrastructure()
    initialize_all_tools()
    
    # Create agent
    agent = MemoryDrivenAgent(project_id)
    
    # Test 1: Simple greeting
    console.print("[yellow]Test 1: Simple greeting[/yellow]")
    response = agent.process_message("你好")
    console.print(f"Response: {response.get('text', 'ERROR')}")
    console.print(f"Skill ID: {response.get('skill_id', 'none')}")
    console.print(f"Success: {response.get('success')}\n")
    
    # Test 2: File operation
    console.print("[yellow]Test 2: File operation request[/yellow]")
    response = agent.process_message("帮我读取 README.md 文件")
    console.print(f"Response: {response.get('text', 'ERROR')[:200]}...")
    console.print(f"Skill ID: {response.get('skill_id', 'none')}")
    console.print(f"Success: {response.get('success')}\n")
    
    # Test 3: Task creation
    console.print("[yellow]Test 3: Task creation[/yellow]")
    response = agent.process_message("帮我创建一个学习 Python 的任务")
    console.print(f"Response: {response.get('text', 'ERROR')[:200]}...")
    console.print(f"Skill ID: {response.get('skill_id', 'none')}")
    console.print(f"Success: {response.get('success')}\n")
    
    console.print("[bold green]✓ All tests completed![/bold green]")


if __name__ == "__main__":
    test_basic_functionality()
