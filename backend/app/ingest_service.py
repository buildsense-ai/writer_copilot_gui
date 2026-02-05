"""
MinerU API 集成服务
用于高保真 PDF 解析
"""
import asyncio
import time
import re
from typing import Dict, List, Optional
from pathlib import Path
import requests
import httpx

from app.config import settings
from app.vector_store import vector_store


class MinerUService:
    """MinerU PDF 解析服务"""

    def __init__(self):
        self.api_url = settings.mineru_api_url
        self.api_token = settings.mineru_api_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }

    async def extract_pdf(
        self,
        file_url: str,
        model_version: str = "vlm"
    ) -> Dict:
        """
        提交 PDF 解析任务

        Args:
            file_url: PDF 文件 URL (支持 HTTP/HTTPS)
            model_version: 模型版本 ("vlm" 或 "standard")

        Returns:
            {
                "task_id": "...",
                "status": "processing"
            }
        """
        payload = {
            "url": file_url,
            "model_version": model_version
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

        if "data" in result:
            return result["data"]
        else:
            raise Exception(f"MinerU API error: {result}")

    async def poll_task_status(
        self,
        task_id: str,
        max_wait: int = 300,
        poll_interval: int = 5
    ) -> Dict:
        """
        轮询任务状态直到完成

        Args:
            task_id: 任务ID
            max_wait: 最大等待时间(秒)
            poll_interval: 轮询间隔(秒)

        Returns:
            {
                "status": "completed",
                "result_url": "...",
                "markdown": "..."
            }
        """
        status_url = f"{self.api_url}/{task_id}"
        start_time = time.time()

        while True:
            # 检查超时
            if time.time() - start_time > max_wait:
                raise TimeoutError(f"Task {task_id} timed out after {max_wait}s")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    status_url,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()

            data = result.get("data", {})
            status = data.get("status")

            # 任务完成
            if status == "completed":
                return data

            # 任务失败
            elif status == "failed":
                error_msg = data.get("error", "Unknown error")
                raise Exception(f"Task {task_id} failed: {error_msg}")

            # 继续等待
            await asyncio.sleep(poll_interval)

    def clean_markdown(self, markdown: str) -> str:
        """
        清洗 Markdown 文本

        Args:
            markdown: 原始 Markdown

        Returns:
            清洗后的 Markdown
        """
        # 移除多余的空行
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # 移除 HTML 注释
        markdown = re.sub(r'<!--.*?-->', '', markdown, flags=re.DOTALL)

        # 规范化标题格式
        markdown = re.sub(r'^(#{1,6})\s*', r'\1 ', markdown, flags=re.MULTILINE)

        return markdown.strip()

    def chunk_by_section(
        self,
        markdown: str,
        max_chunk_size: int = 512,
        overlap: int = 50
    ) -> List[Dict]:
        """
        按章节切分 Markdown

        Args:
            markdown: Markdown 文本
            max_chunk_size: 最大块大小(字符数)
            overlap: 重叠窗口(字符数)

        Returns:
            [
                {
                    "text": "...",
                    "section": "Introduction",
                    "chunk_index": 0
                },
                ...
            ]
        """
        chunks = []
        current_section = "Document"

        # 按二级标题分割
        sections = re.split(r'(^## .+$)', markdown, flags=re.MULTILINE)

        for i in range(len(sections)):
            part = sections[i].strip()
            if not part:
                continue

            # 如果是标题
            if part.startswith('## '):
                current_section = part[3:].strip()
                continue

            # 如果内容太长,进一步切分
            if len(part) > max_chunk_size:
                # 按段落切分
                paragraphs = part.split('\n\n')
                current_chunk = ""

                for para in paragraphs:
                    if len(current_chunk) + len(para) < max_chunk_size:
                        current_chunk += para + "\n\n"
                    else:
                        if current_chunk:
                            chunks.append({
                                "text": current_chunk.strip(),
                                "section": current_section,
                                "chunk_index": len(chunks)
                            })
                        current_chunk = para + "\n\n"

                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "section": current_section,
                        "chunk_index": len(chunks)
                    })
            else:
                chunks.append({
                    "text": part,
                    "section": current_section,
                    "chunk_index": len(chunks)
                })

        return chunks

    async def ingest_pdf(
        self,
        file_url: str,
        project_id: str,
        file_name: str,
        save_markdown: bool = True
    ) -> Dict:
        """
        完整的 PDF 摄取流程

        Args:
            file_url: PDF 文件 URL
            project_id: 项目ID
            file_name: 文件名
            save_markdown: 是否保存 Markdown 文件

        Returns:
            {
                "status": "success",
                "task_id": "...",
                "chunks_count": 42,
                "file_path": "..."
            }
        """
        # 1. 提交解析任务
        task_data = await self.extract_pdf(file_url)
        task_id = task_data.get("task_id")

        # 2. 轮询等待完成
        result = await self.poll_task_status(task_id)

        # 3. 获取 Markdown 结果
        markdown = result.get("markdown", "")
        if not markdown:
            # 如果返回的是URL,需要下载
            result_url = result.get("result_url")
            if result_url:
                async with httpx.AsyncClient() as client:
                    response = await client.get(result_url)
                    markdown = response.text

        # 4. 清洗数据
        cleaned_markdown = self.clean_markdown(markdown)

        # 5. 保存 Markdown 文件
        markdown_path = None
        if save_markdown:
            parsed_dir = Path(settings.get_parsed_files_path())
            markdown_path = parsed_dir / f"{project_id}_{file_name}.md"
            markdown_path.write_text(cleaned_markdown, encoding="utf-8")

        # 6. 切片
        chunks = self.chunk_by_section(cleaned_markdown)

        # 7. 准备元数据
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [
            {
                "source_file": file_name,
                "file_path": file_url,
                "section": chunk["section"],
                "chunk_index": chunk["chunk_index"],
                "page_num": chunk.get("page_num"),
                "project_id": project_id
            }
            for chunk in chunks
        ]

        # 8. 向量化并存入 ChromaDB
        vector_store.add_documents(
            project_id=project_id,
            documents=documents,
            metadatas=metadatas
        )

        return {
            "status": "success",
            "task_id": task_id,
            "chunks_count": len(chunks),
            "markdown_path": str(markdown_path) if markdown_path else None
        }


# 全局实例
mineru_service = MinerUService()
