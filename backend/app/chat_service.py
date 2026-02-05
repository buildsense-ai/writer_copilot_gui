"""
DeepSeek R1 对话服务
支持 RAG 检索和思维链推理
"""
import json
from typing import AsyncGenerator, List, Dict, Optional
from openai import AsyncOpenAI

from app.config import settings
from app.vector_store import vector_store


class ChatService:
    """DeepSeek R1 对话服务"""

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key
        )
        self.model = settings.llm_model

    async def retrieve_context(
        self,
        project_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        从 ChromaDB 检索相关上下文

        Args:
            project_id: 项目ID
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            [
                {
                    "text": "...",
                    "metadata": {...},
                    "distance": 0.23
                },
                ...
            ]
        """
        results = vector_store.search(
            project_id=project_id,
            query=query,
            top_k=top_k
        )

        contexts = []
        for i in range(len(results["documents"])):
            contexts.append({
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
                "distance": results["distances"][i]
            })

        return contexts

    def build_rag_prompt(
        self,
        query: str,
        contexts: List[Dict]
    ) -> str:
        """
        构建 RAG 提示词

        Args:
            query: 用户问题
            contexts: 检索到的上下文

        Returns:
            完整提示词
        """
        if not contexts:
            return query

        # 构建上下文部分
        context_parts = []
        for i, ctx in enumerate(contexts, 1):
            source = ctx["metadata"].get("source_file", "Unknown")
            section = ctx["metadata"].get("section", "")
            text = ctx["text"]

            context_parts.append(
                f"[{i}] 来源: {source}\n"
                f"章节: {section}\n"
                f"内容:\n{text}\n"
            )

        context_str = "\n---\n".join(context_parts)

        # 构建完整提示
        prompt = f"""基于以下参考资料回答问题。如果引用了资料，请使用 [1]、[2] 等标注引用来源。

参考资料:
{context_str}

---

用户问题: {query}

请基于上述参考资料提供详细、准确的回答。如果资料中没有相关信息，请明确说明。"""

        return prompt

    async def chat_stream(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
        use_rag: bool = True,
        messages_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        流式对话

        Args:
            project_id: 项目ID
            query: 用户问题
            top_k: RAG 检索数量
            use_rag: 是否使用 RAG
            messages_history: 历史对话 (可选)

        Yields:
            {
                "type": "search" | "reasoning" | "content_chunk",
                "content": "...",
                "contexts": [...]  # 仅 type=search 时
            }
        """
        # 1. RAG 检索
        contexts = []
        if use_rag:
            contexts = await self.retrieve_context(project_id, query, top_k)
            yield {
                "type": "search",
                "content": f"检索到 {len(contexts)} 条相关资料",
                "contexts": contexts
            }

        # 2. 构建提示词
        if use_rag and contexts:
            final_query = self.build_rag_prompt(query, contexts)
        else:
            final_query = query

        # 3. 构建消息列表
        messages = messages_history or []
        messages.append({
            "role": "user",
            "content": final_query
        })

        # 4. 调用 DeepSeek R1
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.2,
                max_tokens=8192,
                extra_body={"reasoning": {"enabled": True}}
            )

            full_content = ""
            reasoning_trace = ""

            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                # 提取思维链（如果存在）
                reasoning = None
                for attr in ("reasoning", "reasoning_content", "reasoning_details"):
                    value = getattr(delta, attr, None)
                    if value:
                        if isinstance(value, str):
                            reasoning = value
                        else:
                            reasoning = json.dumps(value, ensure_ascii=False)
                        break
                if reasoning:
                    reasoning_trace += reasoning
                    yield {
                        "type": "reasoning",
                        "content": reasoning
                    }

                # 提取回复内容
                content = delta.content
                if content:
                    full_content += content
                    yield {
                        "type": "content_chunk",
                        "content": content
                    }

            # 5. 返回完整响应元数据
            yield {
                "type": "done",
                "full_content": full_content,
                "reasoning_trace": reasoning_trace,
                "contexts": contexts
            }

        except Exception as e:
            yield {
                "type": "error",
                "content": str(e)
            }

    async def chat(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
        use_rag: bool = True,
        messages_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        非流式对话 (收集完整响应)

        Returns:
            {
                "content": "...",
                "reasoning_trace": "...",
                "contexts": [...]
            }
        """
        full_content = ""
        reasoning_trace = ""
        contexts = []

        async for event in self.chat_stream(
            project_id, query, top_k, use_rag, messages_history
        ):
            if event["type"] == "search":
                contexts = event.get("contexts", [])
            elif event["type"] == "content_chunk":
                full_content += event["content"]
            elif event["type"] == "reasoning":
                reasoning_trace += event["content"]
            elif event["type"] == "done":
                full_content = event.get("full_content", full_content)
                reasoning_trace = event.get("reasoning_trace", reasoning_trace)

        return {
            "content": full_content,
            "reasoning_trace": reasoning_trace,
            "contexts": contexts
        }


# 全局实例
chat_service = ChatService()
