"""Setup Todo Skill tools."""
from src.core.skills.tool_registry import get_tool_registry
from src.skills.todo.tools import (
    database_operation,
    DATABASE_OPERATION_SCHEMA,
    DATABASE_OPERATION_VISUALIZATION
)
from src.skills.todo.search_tools import (
    search,
    SEARCH_SCHEMA,
    SEARCH_VISUALIZATION
)


def initialize_todo_tools():
    """Initialize and register Todo Skill tools."""
    registry = get_tool_registry()

    # Register database_operation
    registry.register_tool(
        name="database_operation",
        schema=DATABASE_OPERATION_SCHEMA,
        function=database_operation,
        visualization=DATABASE_OPERATION_VISUALIZATION
    )

    # Register search
    registry.register_tool(
        name="search",
        schema=SEARCH_SCHEMA,
        function=search,
        visualization=SEARCH_VISUALIZATION
    )

    print(f"[Todo Skill] Registered 2 tools")
