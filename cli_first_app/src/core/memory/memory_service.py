"""Memory service for conversation storage and retrieval."""
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from src.infrastructure.database.connection import get_db_connection
from src.infra import get_chroma_client
from src.core.memory.embedding_service import EmbeddingService


class MemoryService:
    """
    Manages conversation memory using SQLite + ChromaDB.
    """
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.embedding_service = EmbeddingService()
        
        # Initialize ChromaDB collection for conversations
        self.chroma = get_chroma_client()
        self.collection = self.chroma.get_or_create_collection(
            name=f"conversations_{project_id}",
            metadata={"hnsw:space": "cosine"}
        )
    
    def write_conversation(
        self,
        session_id: str,
        turn: int,
        speaker: str,
        content: str,
        tool_calls: Optional[List[Dict]] = None,
        tool_results: Optional[List[Dict]] = None
    ) -> int:
        """
        Write a conversation turn to storage.
        
        Args:
            session_id: Session identifier
            turn: Turn number
            speaker: 'user' or 'assistant'
            content: Message content
            tool_calls: Optional tool calls made
            tool_results: Optional tool results
            
        Returns:
            source_id: ID of the inserted record
        """
        # Generate embedding
        embedding = self.embedding_service.generate(content)
        
        # Write to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        
        created_at = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            INSERT INTO mem_source 
            (session_id, turn, speaker, content, tool_calls, tool_results, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            turn,
            speaker,
            content,
            json.dumps(tool_calls) if tool_calls else None,
            json.dumps(tool_results) if tool_results else None,
            created_at
        ))
        
        source_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        # Write to ChromaDB
        chroma_id = f"{session_id}_{turn}_{speaker}"
        self.collection.add(
            ids=[chroma_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{
                "session_id": session_id,
                "speaker": speaker,
                "turn": turn,
                "created_at": created_at
            }]
        )
        
        return source_id
    
    def retrieve_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of turns to retrieve
            
        Returns:
            List of conversation turns
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT source_id, session_id, turn, speaker, content, 
                   tool_calls, tool_results, created_at
            FROM mem_source
            WHERE session_id = ?
            ORDER BY turn DESC
            LIMIT ?
        """, (session_id, limit))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Reverse to get chronological order
        results = []
        for row in reversed(rows):
            results.append({
                "source_id": row["source_id"],
                "session_id": row["session_id"],
                "turn": row["turn"],
                "speaker": row["speaker"],
                "content": row["content"],
                "tool_calls": json.loads(row["tool_calls"]) if row["tool_calls"] else None,
                "tool_results": json.loads(row["tool_results"]) if row["tool_results"] else None,
                "created_at": row["created_at"]
            })
        
        return results
    
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
            List of relevant memories with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate(query)
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        
        # Parse results
        memories = []
        if results["ids"] and len(results["ids"]) > 0:
            ids = results["ids"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0] * len(ids)
            
            for i, memory_id in enumerate(ids):
                distance = distances[i]
                similarity = max(0.0, 1 - distance)
                
                if similarity < similarity_threshold:
                    continue
                
                memories.append({
                    "id": memory_id,
                    "content": documents[i],
                    "metadata": metadatas[i],
                    "similarity": similarity
                })
        
        return memories
