"""Setup file operations tools."""
from src.core.skills.tool_registry import get_tool_registry
from src.skills.file_ops.tools import (
    read_file,
    apply_edit,
    write_file,
    list_files,
    READ_FILE_SCHEMA,
    APPLY_EDIT_SCHEMA,
    WRITE_FILE_SCHEMA,
    LIST_FILES_SCHEMA
)


def initialize_file_ops_tools():
    """Initialize and register file operations tools."""
    registry = get_tool_registry()

    # Register read_file
    registry.register_tool(
        name="read_file",
        schema=READ_FILE_SCHEMA,
        function=read_file
    )

    # Register apply_edit
    registry.register_tool(
        name="apply_edit",
        schema=APPLY_EDIT_SCHEMA,
        function=apply_edit
    )

    # Register write_file
    registry.register_tool(
        name="write_file",
        schema=WRITE_FILE_SCHEMA,
        function=write_file
    )

    # Register list_files
    registry.register_tool(
        name="list_files",
        schema=LIST_FILES_SCHEMA,
        function=list_files
    )

    print(f"[File Operations Skill] Registered 4 tools")
