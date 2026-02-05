"""
记忆驱动 Agent - 核心控制器

功能：
1. Skill 检索和选择
2. 工具动态挂载
3. LLM 对话循环
4. 记忆存储
"""
import json
from typing import Dict, Any, Optional
from uuid import UUID

from src.core.agent.state import get_session_manager
from src.core.agent.prompts import BASE_AGENT_PROMPT
from src.infrastructure.llm.openrouter_client import OpenRouterClient
from src.core.memory.embedding_service import EmbeddingService
from src.core.memory.memory_service import MemoryService
from src.core.skills.skill_service import SkillService
from src.core.skills.filter_service import FilterService
from src.core.skills.tool_registry import get_tool_registry


class MemoryDrivenAgent:
    """记忆驱动的统一 Agent"""

    def __init__(self, project_id: str):
        """
        初始化 Agent

        Args:
            project_id: 项目 ID
        """
        self.project_id = project_id
        self.session_manager = get_session_manager()
        self.max_iterations = 10

        # 服务层
        self.embedding_service = EmbeddingService()
        self.memory_service = MemoryService(project_id)
        self.skill_service = SkillService(project_id)
        self.filter_service = FilterService()

        # 工具注册表
        self.tool_registry = get_tool_registry()

        # LLM 客户端
        self.llm_client = OpenRouterClient()

    def process_message(
        self,
        user_message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理用户消息

        Args:
            user_message: 用户消息
            session_id: 会话 ID（可选）

        Returns:
            处理结果
        """
        try:
            # 获取或创建会话
            if not session_id:
                session_id = self.session_manager.create_session()
            
            session = self.session_manager.get_session(session_id)
            if not session:
                session_id = self.session_manager.create_session()
                session = self.session_manager.get_session(session_id)

            turn = session["turn"]

            # 生成查询 embedding
            query_embedding = self.embedding_service.generate(user_message)

            # 检索候选 skills
            candidate_skills = self.skill_service.retrieve_skills(
                query_embedding,
                top_k=3
            )

            # LLM 过滤选择最相关的 skill
            selected_skill_id = None
            if candidate_skills:
                selected_skill_id = self.filter_service.filter_skills(
                    user_message,
                    candidate_skills
                )

            # 加载 skill 并获取工具集
            tools = []
            skill_prompt = ""
            
            if selected_skill_id:
                skill = self.skill_service.get_skill_by_id(selected_skill_id)
                if skill:
                    skill_prompt = skill.prompt_template
                    tools = self.tool_registry.get_tools_by_names(skill.tool_set)

            # 构建消息
            system_prompt = BASE_AGENT_PROMPT
            if skill_prompt:
                system_prompt += f"\n\n{skill_prompt}"

            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加对话历史
            history = self.memory_service.retrieve_conversation_history(
                session_id,
                limit=5
            )
            for h in history:
                messages.append({
                    "role": h["speaker"],
                    "content": h["content"]
                })

            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})

            # Agent 循环
            iteration = 0
            final_response = ""

            while iteration < self.max_iterations:
                iteration += 1

                # 调用 LLM
                response = self.llm_client.chat_with_reasoning(messages, tools if tools else None)

                content = response["content"]
                tool_calls = response["tool_calls"]

                # 如果有内容，保存
                if content:
                    final_response = content

                # 如果没有工具调用，结束循环
                if not tool_calls:
                    break

                # 执行工具调用
                messages.append({
                    "role": "assistant",
                    "content": content or "",
                    "tool_calls": tool_calls
                })

                for tc in tool_calls:
                    tool_name = tc["function"]["name"]
                    arguments = json.loads(tc["function"]["arguments"])

                    # 执行工具
                    result = self.tool_registry.execute_tool(tool_name, **arguments)

                    # 添加工具结果
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(result, ensure_ascii=False)
                    })

            # 存储对话
            self.memory_service.write_conversation(
                session_id,
                turn,
                "user",
                user_message
            )

            self.memory_service.write_conversation(
                session_id,
                turn,
                "assistant",
                final_response,
                tool_calls=tool_calls if tool_calls else None
            )

            # 增加轮次
            self.session_manager.increment_turn(session_id)

            return {
                "success": True,
                "text": final_response,
                "session_id": session_id,
                "skill_id": selected_skill_id
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
