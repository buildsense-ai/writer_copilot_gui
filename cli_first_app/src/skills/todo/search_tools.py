"""
搜索工具 - search

语义搜索任务或对话历史。
"""
from typing import Dict, Any, List, Optional

from src.services.search_service import SearchService
from src.infra import get_project_id
import os


# Visualization templates
SEARCH_VISUALIZATION = {
    "calling": "【正在搜索 \"{query}\"】",
    "success": "【找到 {count} 个结果】",
    "error": "【✗ 搜索失败：{error}】"
}


# Tool Schema
SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search",
        "description": """语义搜索工具。使用向量相似度搜索任务或对话历史。

使用场景：
- 搜索任务："帮我找关于学习的任务"
- 搜索想法："搜索 brainstorm 状态的任务"
- 清理重复："找出重复的任务"

注意：使用语义搜索，不需要精确匹配关键词。""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询"
                },
                "search_type": {
                    "type": "string",
                    "enum": ["tasks", "conversations", "both"],
                    "description": "搜索类型",
                    "default": "tasks"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量",
                    "default": 10
                },
                "status_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "按状态过滤（仅用于任务搜索）"
                },
                "priority_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "按优先级过滤（仅用于任务搜索）"
                }
            },
            "required": ["query"]
        }
    }
}


def search(
    query: str,
    search_type: str = "tasks",
    limit: int = 10,
    status_filter: Optional[List[str]] = None,
    priority_filter: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    执行语义搜索

    Args:
        query: 搜索查询
        search_type: 搜索类型
        limit: 结果数量
        status_filter: 状态过滤
        priority_filter: 优先级过滤

    Returns:
        搜索结果
    """
    project_id = get_project_id(os.getcwd())
    search_service = SearchService(project_id)

    try:
        results = {}

        if search_type in ["tasks", "both"]:
            tasks = search_service.search_tasks_semantic(
                query=query,
                limit=limit,
                status_filter=status_filter,
                priority_filter=priority_filter
            )

            results["tasks"] = [
                {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                }
                for task in tasks
            ]

        if search_type in ["conversations", "both"]:
            # TODO: 实现对话搜索
            results["conversations"] = []

        return {
            "query": query,
            "search_type": search_type,
            "results": results,
            "count": len(results.get("tasks", [])) + len(results.get("conversations", []))
        }

    except Exception as e:
        import traceback
        return {
            "error": f"Search failed: {str(e)}",
            "traceback": traceback.format_exc()
        }
