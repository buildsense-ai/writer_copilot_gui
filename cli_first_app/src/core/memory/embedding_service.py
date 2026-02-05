"""Embedding service using OpenRouter API."""
import os
from typing import List
from openai import OpenAI


class EmbeddingService:
    """
    Generate embeddings using OpenRouter's Qwen model.
    """
    
    def __init__(self):
        self.model = os.getenv("EMBEDDING_MODEL", "qwen/qwen3-embedding-4b")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
    
    def generate(self, text: str) -> List[float]:
        """
        Generate embedding for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                extra_headers={
                    "HTTP-Referer": "http://localhost:cli-agent",
                    "X-Title": "CLI-Agent"
                }
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")
