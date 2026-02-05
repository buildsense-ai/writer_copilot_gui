"""Filter service for LLM-based filtering of skills."""
from typing import List, Dict, Any, Optional
import json

from src.infrastructure.llm.openrouter_client import OpenRouterClient


class FilterService:
    """LLM 过滤服务"""

    def __init__(self):
        self.llm_client = OpenRouterClient()

    def filter_skills(
        self,
        user_query: str,
        candidate_skills: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        使用 LLM 从候选 skills 中选择最相关的一个

        Args:
            user_query: 用户查询
            candidate_skills: 候选技能列表

        Returns:
            选中的 skill_id，如果都不相关则返回 None
        """
        if not candidate_skills:
            return None

        # 构建 prompt
        skills_desc = "\n".join([
            f"- {skill['id']}: {skill.get('name', skill['id'])} (相似度: {skill.get('similarity', 0):.2f})"
            for skill in candidate_skills
        ])

        prompt = f"""你是一个智能助手，需要根据用户的查询选择最合适的 skill。

用户查询: {user_query}

可用的 skills:
{skills_desc}

请分析用户的查询意图，选择最合适的 skill。如果用户的查询不需要特定的 skill（比如简单问候），返回 "none"。

只返回 skill 的 id 或 "none"，不要有其他内容。"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}]
            )

            skill_id = response.choices[0].message.content.strip().lower()

            if skill_id == "none" or skill_id not in [s["id"] for s in candidate_skills]:
                return None

            return skill_id

        except Exception as e:
            print(f"Warning: Failed to filter skills: {e}")
            # Fallback: return the skill with highest similarity
            if candidate_skills:
                return candidate_skills[0]["id"]
            return None
