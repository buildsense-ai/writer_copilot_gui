"""File operations tools - combined from cli_first_app tools."""
import os
import difflib
import glob
from typing import Dict, Any
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
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        if not os.path.exists(path):
            return f"ERROR: File not found: {path}"

        if not os.path.isfile(path):
            return f"ERROR: Path is not a file: {path}"

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        numbered_lines = []
        for i, line in enumerate(lines, start=1):
            numbered_lines.append(f"{i:4d} | {line.rstrip()}")

        return "\n".join(numbered_lines)

    except Exception as e:
        return f"ERROR reading file: {str(e)}"


def apply_edit(
    path: str,
    search_block: str,
    replace_block: str
) -> str:
    """
    Apply an edit to a file with diff preview and user confirmation.

    Args:
        path: Path to the file (relative or absolute)
        search_block: Exact text to search for (must be unique)
        replace_block: Text to replace it with

    Returns:
        Success or error message
    """
    try:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        if not os.path.exists(path):
            return f"ERROR: File not found: {path}"

        with open(path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        if search_block not in original_content:
            return f"ERROR: Search block not found in file. Make sure the text matches exactly."

        count = original_content.count(search_block)
        if count > 1:
            return f"ERROR: Search block appears {count} times in the file. It must be unique."

        new_content = original_content.replace(search_block, replace_block, 1)

        diff = difflib.unified_diff(
            original_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"{path} (original)",
            tofile=f"{path} (modified)",
            lineterm=""
        )
        diff_text = "".join(diff)

        console.print("\n" + "="*60)
        console.print(Panel.fit(
            f"[bold cyan]Proposed changes to:[/bold cyan] {path}",
            border_style="cyan"
        ))
        console.print()

        syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
        console.print(syntax)
        console.print()

        confirmed = Confirm.ask(
            "[yellow]Apply this change?[/yellow]",
            default=False
        )

        if not confirmed:
            return "Edit cancelled by user."

        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        console.print(f"[green]✓ Successfully applied changes to {path}[/green]")
        return f"SUCCESS: Changes applied to {path}"

    except Exception as e:
        return f"ERROR applying edit: {str(e)}"


def write_file(path: str, content: str) -> str:
    """
    Write content to a file (create or overwrite) with user confirmation.

    Args:
        path: Path to the file (relative or absolute)
        content: Content to write

    Returns:
        Success or error message
    """
    try:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        file_exists = os.path.exists(path)
        action = "overwrite" if file_exists else "create"

        console.print(f"\n[yellow]About to {action} file: {path}[/yellow]")
        console.print(f"[dim]Content length: {len(content)} characters[/dim]")

        if file_exists:
            console.print("[yellow]Warning: This will overwrite the existing file![/yellow]")

        confirmed = Confirm.ask(
            f"[yellow]Proceed to {action} the file?[/yellow]",
            default=False
        )

        if not confirmed:
            return f"Write cancelled by user."

        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        console.print(f"[green]✓ Successfully wrote to {path}[/green]")
        return f"SUCCESS: File written to {path}"

    except Exception as e:
        return f"ERROR writing file: {str(e)}"


def list_files(directory: str = ".", pattern: str = "*", recursive: bool = False) -> str:
    """
    List files in a directory matching a pattern.

    Args:
        directory: Directory to list (default: current directory)
        pattern: Glob pattern to match (default: all files)
        recursive: Whether to search recursively

    Returns:
        Formatted list of files
    """
    try:
        if not os.path.isabs(directory):
            directory = os.path.join(os.getcwd(), directory)

        if not os.path.exists(directory):
            return f"ERROR: Directory not found: {directory}"

        if recursive:
            search_path = os.path.join(directory, "**", pattern)
            files = glob.glob(search_path, recursive=True)
        else:
            search_path = os.path.join(directory, pattern)
            files = glob.glob(search_path)

        if not files:
            return f"No files found matching pattern: {pattern}"

        files.sort()
        result = [f"Files in {directory}:"]
        for f in files:
            rel_path = os.path.relpath(f, directory)
            if os.path.isfile(f):
                size = os.path.getsize(f)
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                result.append(f"  {rel_path} ({size_str})")
            else:
                result.append(f"  {rel_path}/ (directory)")

        return "\n".join(result)

    except Exception as e:
        return f"ERROR listing files: {str(e)}"


# Tool schemas for LLM
READ_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read a file and return its content with line numbers.",
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
}

APPLY_EDIT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "apply_edit",
        "description": "Apply an edit to a file with diff preview and user confirmation.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file"
                },
                "search_block": {
                    "type": "string",
                    "description": "Exact text to search for (must be unique)"
                },
                "replace_block": {
                    "type": "string",
                    "description": "Text to replace it with"
                }
            },
            "required": ["path", "search_block", "replace_block"]
        }
    }
}

WRITE_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write content to a file (create or overwrite) with user confirmation.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write"
                }
            },
            "required": ["path", "content"]
        }
    }
}

LIST_FILES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": "List files in a directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory to list (default: current)"
                },
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern (e.g., '*.py')"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Search recursively"
                }
            }
        }
    }
}
