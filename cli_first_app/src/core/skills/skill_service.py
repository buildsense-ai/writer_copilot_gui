"""Skill service for managing and retrieving skills."""
import json
from typing import List, Dict, Any, Optional

from src.infrastructure.database.connection import get_db_connection
from src.core.memory.embedding_service import EmbeddingService
from src.core.skills.filesystem_skill_loader import FileSystemSkillLoader
from src.infra import get_chroma_client


class SkillService:
    """技能管理服务"""

    def __init__(
        self,
        project_id: str,
        enable_filesystem: bool = True,
        skills_path: str = "skills"
    ):
        self.project_id = project_id
        self.embedding_service = EmbeddingService()
        self.enable_filesystem = enable_filesystem

        # Initialize filesystem loader if enabled
        self.fs_loader = None
        if enable_filesystem:
            self.fs_loader = FileSystemSkillLoader(
                skills_path=skills_path,
                embedding_service=self.embedding_service
            )

        # Initialize ChromaDB for skill embeddings
        self.chroma = get_chroma_client()
        self.collection = self.chroma.get_or_create_collection(
            name=f"skills_{project_id}",
            metadata={"hnsw:space": "cosine"}
        )

    def retrieve_skills(
        self,
        query_embedding: List[float],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        基于 embedding 检索最相关的 skills

        Args:
            query_embedding: 查询的 embedding 向量
            top_k: 返回结果数量

        Returns:
            技能列表
        """
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        skills = []
        if results["ids"] and len(results["ids"]) > 0:
            ids = results["ids"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0] * len(ids)

            for i, skill_id in enumerate(ids):
                distance = distances[i]
                similarity = max(0.0, 1 - distance)

                skills.append({
                    "id": skill_id,
                    "name": metadatas[i].get("name", skill_id),
                    "similarity": similarity
                })

        return skills

    def get_skill_by_id(self, skill_id: str) -> Optional[Any]:
        """
        根据 ID 获取 skill

        Args:
            skill_id: 技能 ID

        Returns:
            Skill 对象
        """
        # Try filesystem first if enabled
        if self.enable_filesystem and self.fs_loader:
            if self.fs_loader.skill_exists(skill_id):
                return self.fs_loader.load_skill(skill_id)

        # Fallback to database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, prompt_template, tool_set
            FROM skills
            WHERE id = ?
        """, (skill_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            from src.infrastructure.database.models import Skill
            return Skill(
                id=row["id"],
                name=row["name"],
                prompt_template=row["prompt_template"],
                tool_set=json.loads(row["tool_set"]) if row["tool_set"] else []
            )

        return None

    def index_skills(self):
        """
        Index all skills from filesystem to ChromaDB.
        """
        if not self.fs_loader:
            return

        skills = self.fs_loader.load_all_skills()

        for skill in skills:
            # Generate embedding for skill
            embedding = self.embedding_service.generate(
                f"{skill.name}\n{skill.prompt_template[:500]}"
            )

            # Add to ChromaDB
            self.collection.upsert(
                ids=[skill.id],
                embeddings=[embedding],
                documents=[skill.prompt_template],
                metadatas=[{"name": skill.name}]
            )
