"""OpenRouter LLM client for unified API access."""
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI


class OpenRouterClient:
    """
    Unified LLM client using OpenRouter API.
    Supports DeepSeek R1 with reasoning capabilities.
    """
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("LLM_MODEL", "deepseek/deepseek-r1")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """
        Send chat completion request.
        
        Args:
            messages: List of message dictionaries
            tools: Optional list of tool definitions
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Chat completion response
        """
        request_params = {
            "model": self.model,
            "messages": messages,
            "extra_headers": {
                "HTTP-Referer": "http://localhost:cli-agent",
                "X-Title": "CLI-Agent"
            }
        }
        
        # Add tools if provided
        if tools:
            request_params["tools"] = tools
        
        # Enable reasoning for DeepSeek R1
        if "deepseek-r1" in self.model.lower():
            if "extra_body" not in request_params:
                request_params["extra_body"] = {}
            request_params["extra_body"]["reasoning"] = {"enabled": True}
        
        # Merge additional kwargs
        request_params.update(kwargs)
        
        if stream:
            return self.client.chat.completions.create(stream=True, **request_params)
        else:
            return self.client.chat.completions.create(**request_params)
    
    def chat_with_reasoning(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Chat with reasoning details extraction.
        
        Args:
            messages: List of message dictionaries
            tools: Optional list of tool definitions
            
        Returns:
            Dictionary containing response content, reasoning, and tool calls
        """
        response = self.chat(messages, tools, stream=False)
        message = response.choices[0].message
        
        return {
            "content": message.content or "",
            "reasoning_details": getattr(message, "reasoning_details", None),
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in (message.tool_calls or [])
            ] if message.tool_calls else None
        }
