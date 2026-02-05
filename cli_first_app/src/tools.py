"""Tools for file operations with user confirmation."""
import os
import difflib
from typing import Optional
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()


def read_file(path: str) -> str:
    """
    Read a file and return its content with line numbers.

    Args:
        path: Path to the file (relative or absolute)

    Returns:
        File content with line numbers in format "line_num | content"
    """
    try:
        # Convert to absolute path if relative
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        if not os.path.exists(path):
            return f"ERROR: File not found: {path}"

        if not os.path.isfile(path):
            return f"ERROR: Path is not a file: {path}"

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Format with line numbers
        numbered_lines = []
        for i, line in enumerate(lines, start=1):
            numbered_lines.append(f"{i:4d} | {line.rstrip()}")

        return "\n".join(numbered_lines)

    except Exception as e:
        return f"ERROR reading file: {str(e)}"


def apply_edit(
    path: str,
    search_block: str,
    replace_block: str,
    auto_confirm: bool = False
) -> str:
    """
    Apply an edit to a file with diff preview and user confirmation.

    Args:
        path: Path to the file (relative or absolute)
        search_block: Exact text to search for (must be unique)
        replace_block: Text to replace it with
        auto_confirm: If True, skip user confirmation (for testing)

    Returns:
        Success or error message
    """
    try:
        # Convert to absolute path if relative
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        if not os.path.exists(path):
            return f"ERROR: File not found: {path}"

        # Read current content
        with open(path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Check if search_block exists
        if search_block not in original_content:
            return f"ERROR: Search block not found in file. Make sure the text matches exactly."

        # Check if search_block is unique
        count = original_content.count(search_block)
        if count > 1:
            return f"ERROR: Search block appears {count} times in the file. It must be unique."

        # Generate new content
        new_content = original_content.replace(search_block, replace_block, 1)

        # Generate diff for user review
        diff = difflib.unified_diff(
            original_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"{path} (original)",
            tofile=f"{path} (modified)",
            lineterm=""
        )
        diff_text = "".join(diff)

        # Show diff to user
        console.print("\n" + "="*60)
        console.print(Panel.fit(
            f"[bold cyan]Proposed changes to:[/bold cyan] {path}",
            border_style="cyan"
        ))
        console.print()

        # Display the diff with syntax highlighting
        syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
        console.print(syntax)
        console.print()

        # Ask for confirmation unless auto_confirm is True
        if not auto_confirm:
            confirmed = Confirm.ask(
                "[yellow]Apply this change?[/yellow]",
                default=False
            )
        else:
            confirmed = True

        if not confirmed:
            return "Edit cancelled by user."

        # Apply the change
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        console.print(f"[green]✓ Successfully applied changes to {path}[/green]")
        return f"SUCCESS: Changes applied to {path}"

    except Exception as e:
        return f"ERROR applying edit: {str(e)}"


def list_files(directory: str = ".", pattern: str = "*") -> str:
    """
    List files in a directory matching a pattern.

    Args:
        directory: Directory to list (default: current directory)
        pattern: Glob pattern to match (default: all files)

    Returns:
        Formatted list of files
    """
    try:
        import glob

        if not os.path.isabs(directory):
            directory = os.path.join(os.getcwd(), directory)

        if not os.path.exists(directory):
            return f"ERROR: Directory not found: {directory}"

        search_path = os.path.join(directory, pattern)
        files = glob.glob(search_path, recursive=True)

        if not files:
            return f"No files found matching pattern: {pattern}"

        # Sort and format
        files.sort()
        result = [f"Files in {directory}:"]
        for f in files:
            rel_path = os.path.relpath(f, directory)
            if os.path.isfile(f):
                size = os.path.getsize(f)
                result.append(f"  {rel_path} ({size} bytes)")
            else:
                result.append(f"  {rel_path}/ (directory)")

        return "\n".join(result)

    except Exception as e:
        return f"ERROR listing files: {str(e)}"


# Tool definitions for LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its content with line numbers. Use this to examine files before editing them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file (relative or absolute)"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_edit",
            "description": "Apply an edit to a file. Shows a diff preview and asks for user confirmation. The search_block must be an exact, unique match from the file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file (relative or absolute)"
                    },
                    "search_block": {
                        "type": "string",
                        "description": "Exact text to search for (must be unique in the file)"
                    },
                    "replace_block": {
                        "type": "string",
                        "description": "Text to replace it with"
                    }
                },
                "required": ["path", "search_block", "replace_block"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory. Useful for exploring the project structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to list (default: current directory)"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to match (e.g., '*.tex', '**/*.py')"
                    }
                },
                "required": []
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: dict) -> str:
    """
    Execute a tool by name with given arguments.

    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments

    Returns:
        Result of the tool execution
    """
    if tool_name == "read_file":
        return read_file(arguments["path"])
    elif tool_name == "apply_edit":
        return apply_edit(
            arguments["path"],
            arguments["search_block"],
            arguments["replace_block"]
        )
    elif tool_name == "list_files":
        return list_files(
            arguments.get("directory", "."),
            arguments.get("pattern", "*")
        )
    else:
        return f"ERROR: Unknown tool: {tool_name}"
