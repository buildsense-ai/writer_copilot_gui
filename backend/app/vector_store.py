"""
ChromaDB 向量存储服务
用于存储和检索文档嵌入向量
"""
from typing import List, Dict, Optional
import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI

from app.config import settings

# 禁用 ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"


class VectorStore:
    """ChromaDB 向量存储管理器"""

    def __init__(self):
        """初始化 ChromaDB 客户端"""
        chroma_path = settings.get_chroma_path()

        # 创建持久化的 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # OpenRouter 客户端用于生成嵌入
        self.embedding_client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key
        )

        # 嵌入模型名称
        self.embedding_model = settings.embedding_model

    def get_or_create_collection(self, project_id: str):
        """获取或创建项目的向量集合"""
        collection_name = f"project_{project_id}"

        # 使用余弦相似度
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        return collection

    def get_embedding(self, text: str) -> List[float]:
        """
        使用 Qwen Embedding 模型生成文本向量

        Args:
            text: 要嵌入的文本

        Returns:
            向量列表 (通常是 1024 或 1536 维)
        """
        try:
            response = self.embedding_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")

    def add_documents(
        self,
        project_id: str,
        documents: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None
    ):
        """
        添加文档到向量数据库

        Args:
            project_id: 项目ID
            documents: 文档文本列表
            metadatas: 元数据列表 (包含 page_num, source_file, bbox 等)
            ids: 文档ID列表 (可选,自动生成)
        """
        collection = self.get_or_create_collection(project_id)

        # 生成嵌入向量
        embeddings = [self.get_embedding(doc) for doc in documents]

        # 如果没有提供ID,使用索引生成
        if ids is None:
            existing_count = collection.count()
            ids = [f"{project_id}_chunk_{existing_count + i}"
                   for i in range(len(documents))]

        # 添加到集合
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        return ids

    def search(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        语义搜索相关文档

        Args:
            project_id: 项目ID
            query: 查询文本
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件

        Returns:
            {
                "ids": [...],
                "documents": [...],
                "metadatas": [...],
                "distances": [...]  # 余弦距离，越小越相似
            }
        """
        collection = self.get_or_create_collection(project_id)

        # 生成查询向量
        query_embedding = self.get_embedding(query)

        # 搜索
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata
        )

        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }

    def delete_document(self, project_id: str, document_id: str):
        """删除单个文档"""
        collection = self.get_or_create_collection(project_id)
        collection.delete(ids=[document_id])

    def delete_collection(self, project_id: str):
        """删除整个项目的向量集合"""
        collection_name = f"project_{project_id}"
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            pass  # 集合不存在时忽略

    def get_collection_stats(self, project_id: str) -> Dict:
        """获取集合统计信息"""
        collection = self.get_or_create_collection(project_id)

        return {
            "name": collection.name,
            "count": collection.count(),
            "metadata": collection.metadata
        }


# 全局实例
vector_store = VectorStore()
