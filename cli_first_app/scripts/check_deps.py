#!/usr/bin/env python3
"""Check if all required dependencies are installed."""
import sys
from rich.console import Console
from rich.table import Table

console = Console()


def check_dependencies():
    """Check if all required packages are installed."""
    required_packages = {
        "openai": "OpenAI SDK (OpenRouter client)",
        "chromadb": "Vector database",
        "rich": "Terminal UI",
        "prompt_toolkit": "Interactive input",
        "dotenv": "Environment variables (python-dotenv)",
        "dateutil": "Date utilities (python-dateutil)",
    }
    
    table = Table(title="Dependency Check")
    table.add_column("Package", style="cyan")
    table.add_column("Description", style="dim")
    table.add_column("Status", style="green")
    
    all_installed = True
    
    for package, description in required_packages.items():
        try:
            if package == "dotenv":
                __import__("dotenv")
            elif package == "dateutil":
                __import__("dateutil")
            else:
                __import__(package)
            
            table.add_row(package, description, "[green]✓ Installed[/green]")
        except ImportError:
            table.add_row(package, description, "[red]✗ Missing[/red]")
            all_installed = False
    
    console.print(table)
    console.print()
    
    if all_installed:
        console.print("[bold green]✓ All required dependencies are installed![/bold green]")
        console.print("\nYou can now run:")
        console.print("  [cyan]python scripts/init_db.py[/cyan]")
        console.print("  [cyan]python chat.py[/cyan]")
    else:
        console.print("[bold red]✗ Some dependencies are missing![/bold red]")
        console.print("\nInstall with:")
        console.print("  [cyan]pip install -r ../requirements.txt[/cyan]")
        console.print("Or:")
        console.print("  [cyan]pip install -r requirements-standalone.txt[/cyan]")
    
    return all_installed


def main():
    """Main entry point."""
    console.print("\n[bold]CLI Agent Dependency Check[/bold]\n")
    success = check_dependencies()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
