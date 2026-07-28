"""
OpenAI LLM client — GPT-4o and compatible models.

Supports vision (image_url in content), native tool calling, and
multi-turn conversations with tool results.
"""

from __future__ import annotations

import os
import json
from .base import LLMProvider, LLMResponse, ToolCall
from .secrets import load_secrets_env


class OpenAIClient(LLMProvider):
    def __init__(self, model: str = "gpt-4o"):
        self._model = model
        self.client = None

        load_secrets_env()

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("[OpenAI] Warning: OPENAI_API_KEY not found. Set it in ~/.mia/secrets.env, config/secrets.env, or .env")
        else:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)

    @property
    def model_name(self) -> str:
        return f"OpenAI ({self._model})"

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        if not self.client:
            return LLMResponse(
                text="OpenAI client not configured. Set OPENAI_API_KEY in ~/.mia/secrets.env, config/secrets.env, or .env"
            )

        kwargs: dict = {
            "model": self._model,
            "messages": messages,  # OpenAI already uses this format natively
        }
        if tools:
            kwargs["tools"] = tools

        try:
            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message

            # --- Tool calls ---
            if message.tool_calls:
                tool_calls = []
                for tc in message.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                    tool_calls.append(ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    ))
                return LLMResponse(
                    text=message.content,
                    tool_calls=tool_calls,
                    raw=response,
                )

            # --- Plain text ---
            return LLMResponse(text=message.content or "", raw=response)

        except Exception as e:
            raise RuntimeError(f"[OpenAI error] {e}") from e
