"""Initialize all skills."""
from src.core.skills.tool_registry import get_tool_registry
from src.skills.file_ops.setup import initialize_file_ops_tools
from src.skills.todo.setup import initialize_todo_tools


def initialize_all_tools():
    """Initialize all skill tools."""
    registry = get_tool_registry()
    
    # Initialize file operations tools
    initialize_file_ops_tools()
    
    # Initialize todo tools
    initialize_todo_tools()
    
    print(f"✓ Initialized {len(registry.tools)} tools total")
