"""Memory management with OpenRouter embeddings and ChromaDB + SQLite."""
import os
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from openai import OpenAI
from rich.console import Console
from src.infra import get_db_connection, get_chroma_client

console = Console()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen/qwen3-embedding-4b")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class MemoryManager:
    """Manages embeddings and vector storage using OpenRouter."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        self.chroma = get_chroma_client()
        self.collection = self.chroma.get_or_create_collection(
            name=f"cli_{project_id}",
            metadata={"hnsw:space": "cosine"}
        )

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding from OpenRouter using qwen3-embedding-4b.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                extra_headers={
                    "HTTP-Referer": "http://localhost:paper-cli",
                    "X-Title": "PaperCLI"
                }
            )
            return response.data[0].embedding
        except Exception as e:
            console.print(f"[red]Error getting embedding: {e}[/red]")
            raise

    def store_memory(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a memory with its embedding in the database.

        Args:
            text: Text to store
            metadata: Optional metadata as a dictionary

        Returns:
            ID of the stored memory
        """
        embedding = self.get_embedding(text)
        memory_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        meta = dict(metadata or {})
        meta["project_id"] = self.project_id
        meta["created_at"] = created_at

        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[meta]
        )

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO memories (id, project_id, text, metadata, created_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                memory_id,
                self.project_id,
                text,
                json.dumps(metadata or {}, ensure_ascii=False),
                created_at,
            )
        )
        conn.commit()
        cursor.close()
        conn.close()

        return memory_id

    def search_memories(
        self,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant memories using vector similarity.

        Args:
            query: Search query
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of memory dictionaries with text, similarity, and metadata
        """
        query_embedding = self.get_embedding(query)

        raw = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )

        ids = raw.get("ids", [[]])[0]
        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]

        results = []
        for i, memory_id in enumerate(ids):
            distance = distances[i] if i < len(distances) else None
            similarity = None if distance is None else max(0.0, 1 - distance)
            if similarity is not None and similarity < similarity_threshold:
                continue
            meta = metadatas[i] if i < len(metadatas) else {}
            results.append({
                "id": memory_id,
                "text": documents[i] if i < len(documents) else "",
                "metadata": meta,
                "similarity": similarity,
            })

        return results

    def get_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all memories for the current project.

        Args:
            limit: Maximum number of memories to retrieve

        Returns:
            List of memory dictionaries
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, text, metadata, created_at
            FROM memories
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT ?;
            """,
            (self.project_id, limit)
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "text": row[1],
                "metadata": json.loads(row[2]) if row[2] else None,
                "created_at": row[3],
            })

        cursor.close()
        conn.close()

        return results

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a specific memory.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            True if deleted, False if not found
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM memories
            WHERE id = ? AND project_id = ?;
            """,
            (memory_id, self.project_id)
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()

        if deleted:
            self.collection.delete(ids=[memory_id])

        return deleted

    def clear_project_memories(self) -> int:
        """
        Clear all memories for the current project.

        Returns:
            Number of memories deleted
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM memories WHERE project_id = ?;",
            (self.project_id,)
        )
        ids = [row[0] for row in cursor.fetchall()]

        cursor.execute(
            "DELETE FROM memories WHERE project_id = ?;",
            (self.project_id,)
        )
        count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        if ids:
            self.collection.delete(ids=ids)

        return count
