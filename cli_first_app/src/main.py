"""Main CLI application using Typer and Rich."""
import os
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.prompt import Prompt
from dotenv import load_dotenv

from src.infra import setup_infrastructure
from src.memory import MemoryManager
from src.llm import ChatSession, create_system_prompt

# Load environment variables
load_dotenv()

app = typer.Typer(
    name="paper",
    help="CLI-based AI assistant for academic paper writing",
    add_completion=False
)
console = Console()


def get_file_tree(directory: str = ".", max_depth: int = 3) -> str:
    """
    Generate a file tree of the project.

    Args:
        directory: Root directory
        max_depth: Maximum depth to traverse

    Returns:
        String representation of the file tree
    """
    def build_tree(path: Path, tree: Tree, current_depth: int = 0):
        if current_depth >= max_depth:
            return

        try:
            paths = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        except PermissionError:
            return

        for p in paths:
            # Skip hidden files and common ignore patterns
            if p.name.startswith('.') or p.name in ['__pycache__', 'node_modules', 'venv', 'env']:
                continue

            if p.is_dir():
                branch = tree.add(f"[bold cyan]{p.name}/[/bold cyan]")
                build_tree(p, branch, current_depth + 1)
            else:
                # Show file with size
                size = p.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                tree.add(f"[green]{p.name}[/green] [dim]({size_str})[/dim]")

    root_path = Path(directory)
    tree = Tree(f"[bold blue]{root_path.absolute()}[/bold blue]")
    build_tree(root_path, tree)

    # Convert to string
    from io import StringIO
    string_io = StringIO()
    temp_console = Console(file=string_io, force_terminal=False, width=100)
    temp_console.print(tree)
    return string_io.getvalue()


@app.command()
def chat(
    message: Optional[str] = typer.Argument(None, help="Initial message to the assistant"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM model to use"),
):
    """
    Start an interactive chat session with the AI assistant.
    """
    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        console.print("[red]Error: OPENROUTER_API_KEY not found in environment.[/red]")
        console.print("[yellow]Please set your OpenRouter API key:[/yellow]")
        console.print("  export OPENROUTER_API_KEY='your-key-here'")
        console.print("[yellow]Or create a .env file with:[/yellow]")
        console.print("  OPENROUTER_API_KEY=your-key-here")
        raise typer.Exit(1)

    # Override model if specified
    if model:
        os.environ["LLM_MODEL"] = model

    try:
        # Setup infrastructure
        console.print(Panel.fit(
            "[bold cyan]Paper-CLI: AI Assistant for Academic Writing[/bold cyan]",
            border_style="cyan"
        ))
        console.print()

        project_id = setup_infrastructure()

        # Initialize memory manager
        memory_manager = MemoryManager(project_id)

        # Get file tree
        console.print("[cyan]Building project context...[/cyan]")
        file_tree = get_file_tree()

        # Get initial message
        if not message:
            console.print()
            console.print("[bold]How can I help you with your paper today?[/bold]")
            message = Prompt.ask("[cyan]You[/cyan]")

        # Search for relevant memories
        memories = memory_manager.search_memories(message, limit=3)

        # Create system prompt
        system_prompt = create_system_prompt(file_tree, memories)

        # Start chat session
        chat_session = ChatSession(project_id, system_prompt)

        # Run conversation loop
        chat_session.run_conversation_loop(message)

        # Store the conversation in memory for future reference
        conversation_summary = f"User asked: {message}"
        memory_manager.store_memory(
            conversation_summary,
            metadata={"type": "conversation", "user_message": message}
        )

        console.print("\n[dim]Session complete. Memory saved for future reference.[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Chat interrupted by user.[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def memories(
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search memories"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of memories to show"),
    clear: bool = typer.Option(False, "--clear", help="Clear all memories for this project"),
):
    """
    Manage conversation memories for the current project.
    """
    try:
        project_id = setup_infrastructure()
        memory_manager = MemoryManager(project_id)

        if clear:
            count = memory_manager.clear_project_memories()
            console.print(f"[green]Cleared {count} memories for this project.[/green]")
            return

        if search:
            console.print(f"[cyan]Searching memories for: {search}[/cyan]\n")
            results = memory_manager.search_memories(search, limit=limit)
        else:
            console.print(f"[cyan]Recent memories:[/cyan]\n")
            results = memory_manager.get_all_memories(limit=limit)

        if not results:
            console.print("[yellow]No memories found.[/yellow]")
            return

        for i, mem in enumerate(results, 1):
            panel_content = mem['text']
            if mem.get('similarity'):
                panel_content += f"\n\n[dim]Similarity: {mem['similarity']:.2f}[/dim]"
            if mem.get('created_at'):
                panel_content += f"\n[dim]Created: {mem['created_at']}[/dim]"

            console.print(Panel(
                panel_content,
                title=f"[bold]Memory {i}[/bold]",
                border_style="blue"
            ))
            console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def info():
    """
    Show information about the current project and configuration.
    """
    try:
        cwd = os.getcwd()
        from src.infra import get_project_id

        console.print(Panel.fit(
            "[bold cyan]Paper-CLI Project Information[/bold cyan]",
            border_style="cyan"
        ))
        console.print()

        console.print(f"[bold]Current Directory:[/bold] {cwd}")
        console.print(f"[bold]Project ID:[/bold] {get_project_id(cwd)}")
        console.print()

        console.print(f"[bold]LLM Model:[/bold] {os.getenv('LLM_MODEL', 'deepseek/deepseek-r1')}")
        console.print(f"[bold]Embedding Model:[/bold] {os.getenv('EMBEDDING_MODEL', 'qwen/qwen3-embedding-4b')}")
        console.print()

        # Show file tree
        console.print("[bold]Project Structure:[/bold]")
        file_tree = get_file_tree()
        console.print(file_tree)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    console.print("[cyan]Paper-CLI v0.1.0[/cyan]")
    console.print("[dim]AI assistant for academic paper writing[/dim]")


if __name__ == "__main__":
    app()
