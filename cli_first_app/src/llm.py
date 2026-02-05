"""LLM chat with OpenRouter and reasoning preservation."""
import os
import json
from typing import List, Dict, Any, Optional, Generator
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from rich.markdown import Markdown

from src.tools import TOOLS, execute_tool

console = Console()

LLM_MODEL = os.getenv("LLM_MODEL", "deepseek/deepseek-r1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class ChatSession:
    """Manages a chat session with OpenRouter, preserving reasoning details."""

    def __init__(self, project_id: str, system_prompt: str):
        self.project_id = project_id
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, Any]] = []
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation history."""
        self.messages.append({
            "role": "user",
            "content": content
        })

    def add_assistant_message(
        self,
        content: str,
        reasoning_details: Optional[Any] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add an assistant message to the conversation history.

        Args:
            content: The assistant's response content
            reasoning_details: Reasoning details from DeepSeek R1 (preserved for context)
            tool_calls: Tool calls made by the assistant
        """
        message = {
            "role": "assistant",
            "content": content
        }

        # Preserve reasoning_details for context continuity
        if reasoning_details is not None:
            message["reasoning_details"] = reasoning_details

        # Add tool calls if present
        if tool_calls:
            message["tool_calls"] = tool_calls

        self.messages.append(message)

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        """Add a tool result to the conversation history."""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })

    def _show_reasoning(self, reasoning_content: str) -> None:
        """Display reasoning in a collapsible/minimal way."""
        # Show a spinner with minimal text
        # In production, could make this expandable
        console.print(f"[dim]🧠 Thinking...[/dim]", end="\r")

    def chat(
        self,
        user_message: Optional[str] = None,
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        Send a message and get a response from the LLM.

        Args:
            user_message: User message to send (optional if continuing from tool use)
            stream: Whether to stream the response

        Returns:
            Dictionary containing the response and any tool calls
        """
        if user_message:
            self.add_user_message(user_message)

        # Prepare messages for API call
        api_messages = [{"role": "system", "content": self.system_prompt}]
        api_messages.extend(self.messages)

        try:
            if stream:
                return self._chat_stream(api_messages)
            else:
                return self._chat_sync(api_messages)
        except Exception as e:
            console.print(f"[red]Error in chat: {e}[/red]")
            raise

    def _chat_sync(self, api_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synchronous (non-streaming) chat - ensures reasoning_details are captured.

        This is the recommended approach for MVP to properly capture reasoning_details.
        """
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=api_messages,
            tools=TOOLS,
            extra_body={"reasoning": {"enabled": True}},
            extra_headers={
                "HTTP-Referer": "http://localhost:paper-cli",
                "X-Title": "PaperCLI"
            }
        )

        message = response.choices[0].message

        # Extract reasoning details
        reasoning_details = getattr(message, "reasoning_details", None)

        # Show reasoning if present
        if reasoning_details:
            # For DeepSeek R1, reasoning might be in different formats
            # Try to extract the actual reasoning text
            if hasattr(reasoning_details, "content"):
                self._show_reasoning(reasoning_details.content)
            elif isinstance(reasoning_details, dict) and "content" in reasoning_details:
                self._show_reasoning(reasoning_details["content"])

        # Display the assistant's response
        content = message.content or ""
        if content:
            console.print()
            console.print(Panel(
                Markdown(content),
                title="[bold cyan]Assistant[/bold cyan]",
                border_style="cyan"
            ))

        # Handle tool calls
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]

        # Add to history
        self.add_assistant_message(
            content=content,
            reasoning_details=reasoning_details,
            tool_calls=tool_calls
        )

        return {
            "content": content,
            "reasoning_details": reasoning_details,
            "tool_calls": tool_calls
        }

    def _chat_stream(self, api_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Streaming chat - more complex but better UX.

        Note: Capturing reasoning_details in streaming mode may vary by OpenRouter's implementation.
        For MVP, we use sync mode to ensure correct reasoning preservation.
        """
        # For now, fall back to sync mode to ensure reasoning is captured correctly
        console.print("[yellow]Note: Using sync mode to preserve reasoning details[/yellow]")
        return self._chat_sync(api_messages)

    def execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> bool:
        """
        Execute tool calls and add results to conversation.

        Args:
            tool_calls: List of tool calls from the assistant

        Returns:
            True if tools were executed, False if there was an error
        """
        for tc in tool_calls:
            tool_name = tc["function"]["name"]
            arguments = json.loads(tc["function"]["arguments"])

            console.print(f"\n[yellow]🔧 Executing tool: {tool_name}[/yellow]")
            console.print(f"[dim]Arguments: {arguments}[/dim]")

            # Execute the tool
            result = execute_tool(tool_name, arguments)

            # Add result to conversation
            self.add_tool_result(tc["id"], result)

            # Show result
            console.print(Panel(
                result,
                title=f"[bold green]Tool Result: {tool_name}[/bold green]",
                border_style="green"
            ))

        return True

    def run_conversation_loop(self, initial_message: str) -> None:
        """
        Run the full conversation loop with tool execution.

        Args:
            initial_message: Initial user message
        """
        # Send initial message
        response = self.chat(initial_message, stream=False)

        # Loop while there are tool calls
        max_iterations = 10  # Prevent infinite loops
        iteration = 0

        while response.get("tool_calls") and iteration < max_iterations:
            iteration += 1

            # Execute tools
            self.execute_tool_calls(response["tool_calls"])

            # Continue conversation with tool results
            response = self.chat(user_message=None, stream=False)

        if iteration >= max_iterations:
            console.print("[red]Warning: Maximum iteration limit reached[/red]")


def create_system_prompt(
    file_tree: str,
    memories: List[Dict[str, Any]]
) -> str:
    """
    Create the system prompt with file tree and relevant memories.

    Args:
        file_tree: File tree of the current project
        memories: Relevant memories from vector search

    Returns:
        Complete system prompt
    """
    memories_text = ""
    if memories:
        memories_text = "\n\n## Relevant Context from Previous Sessions\n"
        for i, mem in enumerate(memories, 1):
            memories_text += f"\n{i}. {mem['text']}\n"
            if mem.get("metadata"):
                memories_text += f"   (Similarity: {mem.get('similarity', 0):.2f})\n"

    return f"""You are an AI assistant specialized in academic paper writing and LaTeX editing.

You help researchers write, edit, and improve their academic papers. You have access to tools to read and edit files.

## Current Project Structure
{file_tree}
{memories_text}

## Your Capabilities
- Read and analyze LaTeX files, bibliographies, and related documents
- Suggest improvements to writing, structure, and clarity
- Help with LaTeX formatting and compilation issues
- Apply precise edits to files with user confirmation
- Maintain context across the conversation

## Guidelines
- Always read a file before suggesting edits
- Be precise and academic in your suggestions
- Show diffs before applying changes
- Ask for clarification when needed
- Respect the author's voice and style

When using tools:
- Use read_file to examine files before editing
- Use apply_edit to make changes (user will confirm via diff preview)
- Use list_files to explore the project structure
"""
