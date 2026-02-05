#!/usr/bin/env python3
"""Verify the integration is working correctly."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table

console = Console()


def check_file_structure():
    """Check if all required files exist."""
    console.print("[cyan]Checking file structure...[/cyan]")
    
    required_files = [
        # Infrastructure
        "src/infrastructure/database/connection.py",
        "src/infrastructure/database/models.py",
        "src/infrastructure/llm/openrouter_client.py",
        "src/infrastructure/utils/cli_colors.py",
        
        # Core
        "src/core/memory/embedding_service.py",
        "src/core/memory/memory_service.py",
        "src/core/skills/tool_registry.py",
        "src/core/skills/filesystem_skill_loader.py",
        "src/core/skills/skill_service.py",
        "src/core/skills/filter_service.py",
        "src/core/agent/memory_driven_agent.py",
        "src/core/agent/prompts.py",
        "src/core/agent/state.py",
        
        # Skills
        "skills/file_ops/config.json",
        "skills/file_ops/skill.md",
        "skills/todo/config.json",
        "skills/todo/skill.md",
        "src/skills/file_ops/tools.py",
        "src/skills/file_ops/setup.py",
        "src/skills/todo/tools.py",
        "src/skills/todo/search_tools.py",
        "src/skills/todo/setup.py",
        "src/skills/initialize.py",
        
        # Repositories & Services
        "src/repositories/base.py",
        "src/repositories/task_repository.py",
        "src/repositories/tag_repository.py",
        "src/services/search_service.py",
        
        # Entry points
        "chat.py",
        "scripts/init_db.py",
    ]
    
    table = Table(title="File Structure Check")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    
    all_exist = True
    for file_path in required_files:
        full_path = Path(__file__).parent.parent / file_path
        exists = full_path.exists()
        status = "✓" if exists else "✗"
        color = "green" if exists else "red"
        table.add_row(file_path, f"[{color}]{status}[/{color}]")
        if not exists:
            all_exist = False
    
    console.print(table)
    
    if all_exist:
        console.print("\n[bold green]✓ All required files exist![/bold green]")
    else:
        console.print("\n[bold red]✗ Some files are missing![/bold red]")
    
    return all_exist


def check_tool_registration():
    """Check if tools are registered correctly."""
    console.print("\n[cyan]Checking tool registration...[/cyan]")
    
    from src.skills.initialize import initialize_all_tools
    from src.core.skills.tool_registry import get_tool_registry
    
    initialize_all_tools()
    registry = get_tool_registry()
    
    expected_tools = [
        "read_file",
        "apply_edit",
        "write_file",
        "list_files",
        "database_operation",
        "search"
    ]
    
    table = Table(title="Tool Registration")
    table.add_column("Tool", style="cyan")
    table.add_column("Status", style="green")
    
    all_registered = True
    for tool_name in expected_tools:
        registered = tool_name in registry.tools
        status = "✓" if registered else "✗"
        color = "green" if registered else "red"
        table.add_row(tool_name, f"[{color}]{status}[/{color}]")
        if not registered:
            all_registered = False
    
    console.print(table)
    console.print(f"\nTotal tools registered: {len(registry.tools)}")
    
    if all_registered:
        console.print("[bold green]✓ All tools registered correctly![/bold green]")
    else:
        console.print("[bold red]✗ Some tools are missing![/bold red]")
    
    return all_registered


def check_skills():
    """Check if skills are loadable."""
    console.print("\n[cyan]Checking skills...[/cyan]")
    
    from src.core.skills.filesystem_skill_loader import FileSystemSkillLoader
    
    loader = FileSystemSkillLoader()
    skills = loader.load_all_skills()
    
    table = Table(title="Skills")
    table.add_column("Skill ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Tools", style="yellow")
    
    for skill in skills:
        tools = ", ".join(skill.tool_set) if skill.tool_set else "None"
        table.add_row(skill.id, skill.name, tools)
    
    console.print(table)
    console.print(f"\nTotal skills loaded: {len(skills)}")
    
    if len(skills) >= 2:
        console.print("[bold green]✓ Skills loaded successfully![/bold green]")
        return True
    else:
        console.print("[bold yellow]⚠ Expected at least 2 skills[/bold yellow]")
        return False


def main():
    """Run all verification checks."""
    console.print("\n[bold]CLI Agent Integration Verification[/bold]\n")
    
    results = []
    
    # Check 1: File structure
    results.append(("File Structure", check_file_structure()))
    
    # Check 2: Tool registration
    results.append(("Tool Registration", check_tool_registration()))
    
    # Check 3: Skills
    results.append(("Skills Loading", check_skills()))
    
    # Summary
    console.print("\n" + "="*60)
    console.print("\n[bold]Verification Summary[/bold]\n")
    
    summary_table = Table()
    summary_table.add_column("Check", style="cyan")
    summary_table.add_column("Result", style="green")
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        color = "green" if result else "red"
        summary_table.add_row(check_name, f"[{color}]{status}[/{color}]")
    
    console.print(summary_table)
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        console.print("\n[bold green]🎉 All checks passed! System is ready to use.[/bold green]")
        console.print("\n[cyan]Run: python chat.py[/cyan]")
    else:
        console.print("\n[bold red]Some checks failed. Please review the errors above.[/bold red]")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
