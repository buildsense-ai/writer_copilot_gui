"""
PaperMem FastAPI 后端服务
"""
import os
import json
from typing import Any, AsyncGenerator, Dict, List, Optional
from datetime import datetime

# 禁用 ChromaDB telemetry（必须在导入 chromadb 之前）
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File as FastAPIFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, init_db
from app.models import ChatMessage, ChatSession, Project, File, beijing_now
from app.chat_service import chat_service
from app.ingest_service import mineru_service
from app.vector_store import vector_store
from app.schemas import (
    ChatSessionCreate,
    ChatSessionRead,
    ChatMessageRead,
    ProjectCreate,
    ProjectRead,
    FileResponse,
)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="PaperMem - 本地化科研 Copilot"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allow_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """启动时初始化数据库"""
    init_db()
    print(f"""
    ╔══════════════════════════════════════╗
    ║   PaperMem Backend Server Started    ║
    ║   Version: {settings.app_version}                     ║
    ║   Environment: {settings.environment}          ║
    ╚══════════════════════════════════════╝

    SQLite DB: {settings.get_sqlite_path()}
    ChromaDB: {settings.get_chroma_path()}
    """)


# ==================== 健康检查 ====================

@app.get("/health")
def health() -> Dict[str, str]:
    """健康检查端点"""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version
    }


# ==================== 项目管理 ====================

@app.get("/projects", response_model=List[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    """获取所有项目列表"""
    return db.query(Project).order_by(Project.created_at.desc()).all()


@app.post("/projects", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    """创建新项目"""
    project = Project(
        name=payload.name,
        type=payload.type,
        description=payload.description,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)) -> Dict[str, bool]:
    """删除项目及其所有数据"""
    # 删除向量数据
    vector_store.delete_collection(project_id)

    # 删除数据库记录
    db.query(ChatMessage).filter(ChatMessage.project_id == project_id).delete()
    db.query(ChatSession).filter(ChatSession.project_id == project_id).delete()
    db.query(File).filter(File.project_id == project_id).delete()
    deleted = db.query(Project).filter(Project.id == project_id).delete()

    db.commit()
    return {"ok": deleted > 0}


@app.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """获取项目详情"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ==================== 文件管理 ====================

@app.post("/projects/{project_id}/upload")
async def upload_file(
    project_id: str,
    file_url: str,
    file_name: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    上传并解析文件 (MinIO URL)

    Args:
        project_id: 项目ID
        file_url: 文件URL (MinIO 或 HTTP)
        file_name: 文件名

    Returns:
        {
            "file_id": "...",
            "status": "processing",
            "task_id": "..."
        }
    """
    # 创建文件记录
    file_record = File(
        project_id=project_id,
        file_name=file_name,
        file_url=file_url,
        file_type="pdf",
        parse_status="pending"
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)

    try:
        # 异步提交 MinerU 解析任务
        result = await mineru_service.ingest_pdf(
            file_url=file_url,
            project_id=project_id,
            file_name=file_name
        )

        # 更新文件记录
        file_record.mineru_task_id = result.get("task_id")
        file_record.parse_status = "completed"
        file_record.markdown_path = result.get("markdown_path")
        file_record.chunks_count = result.get("chunks_count", 0)
        file_record.parsed_at = beijing_now()

        # 更新项目文件计数
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.file_count = (project.file_count or 0) + 1
            project.last_active_at = beijing_now()

        db.commit()

        return {
            "file_id": file_record.id,
            "status": "completed",
            "task_id": result.get("task_id"),
            "chunks_count": result.get("chunks_count")
        }

    except Exception as e:
        file_record.parse_status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.get("/projects/{project_id}/files", response_model=List[FileResponse])
def list_files(project_id: str, db: Session = Depends(get_db)):
    """获取项目所有文件"""
    return db.query(File).filter(File.project_id == project_id).all()


# ==================== 对话会话管理 ====================

@app.post("/chat_sessions", response_model=ChatSessionRead)
def create_chat_session(
    payload: ChatSessionCreate,
    db: Session = Depends(get_db)
):
    """创建新对话会话"""
    session = ChatSession(
        project_id=payload.project_id,
        title=payload.title
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_or_create_current_session(db: Session, project_id: str):
    """获取或创建当前会话"""
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.project_id == project_id,
            ChatSession.is_current.is_(True)
        )
        .order_by(ChatSession.created_at.desc())
        .first()
    )
    if session:
        return session

    session = ChatSession(project_id=project_id, title="Main")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def save_message(
    db: Session,
    project_id: str,
    session_id: str,
    role: str,
    content: str,
    reasoning_trace: Optional[str] = None,
    search_results: Optional[str] = None,
):
    """保存对话消息"""
    message_count = (
        db.query(func.count(ChatMessage.id))
        .filter(ChatMessage.session_id == session_id)
        .scalar() or 0
    )

    message = ChatMessage(
        session_id=session_id,
        project_id=project_id,
        role=role,
        content=content,
        reasoning_trace=reasoning_trace,
        search_results=search_results,
        has_thinking=bool(reasoning_trace),
        message_index=message_count + 1,
    )
    db.add(message)

    # 更新会话
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.message_count = message_count + 1
        session.last_message_at = beijing_now()

    # 更新项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.message_count = (project.message_count or 0) + 1
        project.last_message_preview = (content or "")[:200]
        project.last_active_at = beijing_now()

    db.commit()
    db.refresh(message)
    return message


@app.get("/projects/{project_id}/messages", response_model=List[ChatMessageRead])
def get_project_messages(
    project_id: str,
    db: Session = Depends(get_db)
) -> List[ChatMessage]:
    """获取项目消息历史"""
    session = get_or_create_current_session(db, project_id)
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.message_index.asc())
        .all()
    )
    return messages


# ==================== RAG 对话 ====================

@app.post("/chat/stream")
async def chat_stream_endpoint(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    流式 RAG 对话

    Request:
        {
            "query": "用户问题",
            "project_id": "项目ID",
            "top_k": 5  # 可选
        }

    Response: SSE 流
        - type: "search" - 检索结果
        - type: "reasoning" - 思考过程
        - type: "content_chunk" - 回复内容片段
        - type: "done" - 完成
    """
    query = payload.get("query")
    project_id = payload.get("project_id")
    top_k = payload.get("top_k", 5)

    if not query or not project_id:
        raise HTTPException(
            status_code=400,
            detail="query 和 project_id 为必填参数"
        )

    session = get_or_create_current_session(db, project_id)

    async def event_stream() -> AsyncGenerator[str, None]:
        full_content = ""
        full_reasoning = ""
        contexts = []

        try:
            async for event in chat_service.chat_stream(
                project_id=project_id,
                query=query,
                top_k=top_k
            ):
                if event["type"] == "search":
                    contexts = event.get("contexts", [])
                elif event["type"] == "content_chunk":
                    full_content += event["content"]
                elif event["type"] == "reasoning":
                    full_reasoning += event["content"]
                elif event["type"] == "done":
                    full_content = event.get("full_content", full_content)
                    full_reasoning = event.get("reasoning_trace", full_reasoning)

                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            # 保存消息
            if full_content:
                save_message(db, project_id, session.id, "user", query)
                save_message(
                    db,
                    project_id,
                    session.id,
                    "assistant",
                    full_content,
                    reasoning_trace=full_reasoning,
                    search_results=json.dumps(contexts, ensure_ascii=False)
                )

        except Exception as e:
            error_event = {
                "type": "error",
                "content": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/chat")
async def chat_endpoint(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """非流式 RAG 对话"""
    query = payload.get("query")
    project_id = payload.get("project_id")
    top_k = payload.get("top_k", 5)

    if not query or not project_id:
        raise HTTPException(
            status_code=400,
            detail="query 和 project_id 为必填参数"
        )

    session = get_or_create_current_session(db, project_id)

    result = await chat_service.chat(
        project_id=project_id,
        query=query,
        top_k=top_k
    )

    # 保存消息
    save_message(db, project_id, session.id, "user", query)
    save_message(
        db,
        project_id,
        session.id,
        "assistant",
        result["content"],
        reasoning_trace=result["reasoning_trace"],
        search_results=json.dumps(result["contexts"], ensure_ascii=False)
    )

    return result


# ==================== 向量搜索 ====================

@app.post("/search")
async def search_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    语义搜索

    Request:
        {
            "query": "搜索内容",
            "project_id": "项目ID",
            "top_k": 5
        }
    """
    query = payload.get("query")
    project_id = payload.get("project_id")
    top_k = payload.get("top_k", 5)

    if not query or not project_id:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    results = vector_store.search(project_id, query, top_k)

    return {
        "query": query,
        "results": [
            {
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
                "distance": results["distances"][i]
            }
            for i in range(len(results["documents"]))
        ]
    }


# ==================== 统计信息 ====================

@app.get("/projects/{project_id}/stats")
def get_project_stats(
    project_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取项目统计信息"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    file_count = db.query(func.count(File.id)).filter(File.project_id == project_id).scalar()
    message_count = db.query(func.count(ChatMessage.id)).filter(ChatMessage.project_id == project_id).scalar()

    # 获取向量集合统计
    vector_stats = vector_store.get_collection_stats(project_id)

    return {
        "project_id": project_id,
        "project_name": project.name,
        "files_count": file_count,
        "messages_count": message_count,
        "vectors_count": vector_stats.get("count", 0),
        "last_active_at": project.last_active_at.isoformat() if project.last_active_at else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=(settings.environment == "development")
    )
