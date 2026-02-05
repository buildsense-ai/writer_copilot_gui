#!/usr/bin/env python3
"""Initialize database and ChromaDB collections."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from rich.console import Console

from src.infrastructure.database.connection import init_database
from src.infra import setup_infrastructure, get_project_id
from src.core.skills.skill_service import SkillService
from src.skills.initialize import initialize_all_tools

load_dotenv()
console = Console()


def main():
    """Initialize database and load skills."""
    console.print("[cyan]Initializing database...[/cyan]")
    
    # Initialize infrastructure
    project_id = setup_infrastructure()
    
    # Initialize database tables
    init_database()
    console.print("[green]✓ Database tables created[/green]")
    
    # Initialize tools
    initialize_all_tools()
    console.print("[green]✓ Tools registered[/green]")
    
    # Index skills
    skill_service = SkillService(project_id)
    skill_service.index_skills()
    console.print("[green]✓ Skills indexed to ChromaDB[/green]")
    
    console.print("\n[bold green]Database initialization complete![/bold green]")
    console.print(f"Project ID: {project_id[:16]}...")
    console.print("\nYou can now run: [cyan]python chat.py[/cyan]")


if __name__ == "__main__":
    main()
