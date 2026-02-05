"""Search service for Todo Skill."""
from typing import List, Optional

from src.repositories.task_repository import TaskRepository
from src.core.memory.embedding_service import EmbeddingService
from src.infra import get_chroma_client, get_project_id
from src.infrastructure.database.models import Task


class SearchService:
    """Service for semantic task search."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.task_repo = TaskRepository()
        self.embedding_service = EmbeddingService()
        
        # Initialize ChromaDB collection for tasks
        self.chroma = get_chroma_client()
        self.collection = self.chroma.get_or_create_collection(
            name=f"tasks_{project_id}",
            metadata={"hnsw:space": "cosine"}
        )
    
    def index_task(self, task: Task, embedding: List[float]):
        """Index a task with its embedding."""
        content = f"{task.title}\n{task.description or ''}"
        
        self.collection.upsert(
            ids=[task.id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{
                "title": task.title,
                "status": task.status or "",
                "priority": task.priority or ""
            }]
        )
    
    def search_tasks_semantic(
        self,
        query: str,
        limit: int = 10,
        status_filter: Optional[List[str]] = None,
        priority_filter: Optional[List[str]] = None
    ) -> List[Task]:
        """
        Semantic search for tasks.
        
        Args:
            query: Search query
            limit: Maximum number of results
            status_filter: Filter by status
            priority_filter: Filter by priority
            
        Returns:
            List of matching tasks
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate(query)
        
        # Build where filter
        where_filter = {}
        if status_filter or priority_filter:
            where_filter = {"$and": []}
            if status_filter:
                where_filter["$and"].append({"status": {"$in": status_filter}})
            if priority_filter:
                where_filter["$and"].append({"priority": {"$in": priority_filter}})
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter if where_filter.get("$and") else None
        )
        
        # Get full task objects
        tasks = []
        if results["ids"] and len(results["ids"]) > 0:
            task_ids = results["ids"][0]
            for task_id in task_ids:
                task = self.task_repo.get_by_id(task_id)
                if task:
                    tasks.append(task)
        
        return tasks
