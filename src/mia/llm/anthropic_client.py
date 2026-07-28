"""
Anthropic LLM client — Claude models.

Translates between the OpenAI-style message/tool format used internally
by Mia and Anthropic's native API format.
"""

from __future__ import annotations

import os
import json
import uuid
from .base import LLMProvider, LLMResponse, ToolCall


class AnthropicClient(LLMProvider):
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self._model = model
        self.client = None

        from dotenv import load_dotenv
        secrets_path = os.path.expanduser("~/.mia/secrets.env")
        if os.path.exists(secrets_path):
            load_dotenv(secrets_path)

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("[Anthropic] Warning: ANTHROPIC_API_KEY not found. Set it in ~/.mia/secrets.env")
        else:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=api_key)
            except ImportError:
                print("[Anthropic] Warning: anthropic package not installed.")

    @property
    def model_name(self) -> str:
        return f"Anthropic ({self._model})"

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        if not self.client:
            return LLMResponse(
                text="Anthropic client not configured. Set ANTHROPIC_API_KEY in ~/.mia/secrets.env"
            )

        # --- Separate system prompt from messages ---
        system_prompt = None
        conversation: list[dict] = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
            elif msg["role"] == "tool":
                # Anthropic: tool results go as user messages with tool_result content blocks
                conversation.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", str(uuid.uuid4())[:8]),
                        "content": msg.get("content", ""),
                    }],
                })
            elif msg["role"] == "assistant":
                content = msg.get("content", "")
                # If the assistant message had tool calls, reconstruct them
                if msg.get("tool_calls"):
                    blocks = []
                    if content:
                        blocks.append({"type": "text", "text": content})
                    for tc in msg["tool_calls"]:
                        blocks.append({
                            "type": "tool_use",
                            "id": tc.get("id", str(uuid.uuid4())[:8]),
                            "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"])
                            if isinstance(tc["function"]["arguments"], str)
                            else tc["function"]["arguments"],
                        })
                    conversation.append({"role": "assistant", "content": blocks})
                else:
                    conversation.append({"role": "assistant", "content": content if isinstance(content, str) else str(content)})
            elif msg["role"] == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    # Multimodal — translate image_url to Anthropic's source format
                    blocks = []
                    for part in content:
                        if isinstance(part, dict):
                            if part.get("type") == "text":
                                blocks.append({"type": "text", "text": part["text"]})
                            elif part.get("type") == "image_url":
                                url = part.get("image_url", {}).get("url", "")
                                if url.startswith("data:"):
                                    media_type = url.split(";")[0].split(":")[1]
                                    b64_data = url.split(",", 1)[-1]
                                    blocks.append({
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": media_type,
                                            "data": b64_data,
                                        },
                                    })
                        elif isinstance(part, str):
                            blocks.append({"type": "text", "text": part})
                    conversation.append({"role": "user", "content": blocks})
                else:
                    conversation.append({"role": "user", "content": str(content)})

        # --- Merge consecutive same-role messages (Anthropic requires alternating) ---
        conversation = self._merge_consecutive(conversation)

        # --- Convert tools to Anthropic format ---
        anthropic_tools = None
        if tools:
            anthropic_tools = []
            for t in tools:
                fn = t.get("function", {})
                anthropic_tools.append({
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
                })

        # --- API call ---
        kwargs: dict = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": conversation,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        try:
            response = self.client.messages.create(**kwargs)

            text_parts = []
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    ))

            return LLMResponse(
                text="\n".join(text_parts) if text_parts else None,
                tool_calls=tool_calls,
                raw=response,
            )

        except Exception as e:
            raise RuntimeError(f"[Anthropic error] {e}") from e

    @staticmethod
    def _merge_consecutive(messages: list[dict]) -> list[dict]:
        """Anthropic requires alternating user/assistant roles.
        Merge consecutive same-role messages into one."""
        if not messages:
            return messages
        merged = [messages[0]]
        for msg in messages[1:]:
            if msg["role"] == merged[-1]["role"]:
                prev_content = merged[-1]["content"]
                curr_content = msg["content"]
                # Combine into a list of content blocks
                if isinstance(prev_content, str):
                    prev_content = [{"type": "text", "text": prev_content}]
                if isinstance(curr_content, str):
                    curr_content = [{"type": "text", "text": curr_content}]
                if isinstance(prev_content, list) and isinstance(curr_content, list):
                    merged[-1]["content"] = prev_content + curr_content
                else:
                    merged[-1]["content"] = str(prev_content) + "\n" + str(curr_content)
            else:
                merged.append(msg)
        return merged
