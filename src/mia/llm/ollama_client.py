"""
Ollama LLM client — local inference via the Ollama API.

Supports native tool calling (Ollama >= 0.4) and vision models.
Falls back to plain text if the model doesn't support tools.
"""

from __future__ import annotations

import json
import uuid
from .base import LLMProvider, LLMResponse, ToolCall


class OllamaClient(LLMProvider):
    def __init__(self, model: str = "qwen2.5vl:7b"):
        self._model = model

    @property
    def model_name(self) -> str:
        return f"Ollama ({self._model})"

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        import ollama

        # Ollama expects its own message format — mostly OpenAI-compatible
        # but images go in a top-level "images" key per message.
        ollama_messages = self._convert_messages(messages)

        kwargs: dict = {}
        if tools:
            kwargs["tools"] = tools

        try:
            try:
                response = ollama.chat(
                    model=self._model,
                    messages=ollama_messages,
                    **kwargs,
                )
            except Exception as e:
                if "does not support tools" in str(e) and tools:
                    # Model doesn't support native tool calling — retry without tools
                    kwargs.pop("tools", None)
                    response = ollama.chat(
                        model=self._model,
                        messages=ollama_messages,
                        **kwargs,
                    )
                else:
                    raise

            message = response.get("message", {})

            # --- Tool calls ---
            if message.get("tool_calls"):
                tool_calls = []
                for tc in message["tool_calls"]:
                    fn = tc.get("function", {})
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}
                    tool_calls.append(ToolCall(
                        id=str(uuid.uuid4())[:8],
                        name=fn.get("name", ""),
                        arguments=args,
                    ))
                return LLMResponse(tool_calls=tool_calls, raw=response)

            # --- Plain text ---
            return LLMResponse(text=message.get("content", ""), raw=response)

        except Exception as e:
            return LLMResponse(text=f"[Ollama error] {e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _convert_messages(messages: list[dict]) -> list[dict]:
        """Convert OpenAI-style messages to Ollama format.

        Key difference: Ollama wants images as a list of base64 strings
        in a top-level ``images`` key, not embedded in the ``content`` array.
        """
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Tool-result messages → map to Ollama's expected format
            if role == "tool":
                converted.append({
                    "role": "tool",
                    "content": content if isinstance(content, str) else json.dumps(content),
                })
                continue

            # If content is a list (multimodal), extract text + images
            if isinstance(content, list):
                texts = []
                images = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            texts.append(part["text"])
                        elif part.get("type") == "image_url":
                            url = part.get("image_url", {}).get("url", "")
                            if url.startswith("data:"):
                                # Extract base64 data
                                b64 = url.split(",", 1)[-1]
                                images.append(b64)
                    elif isinstance(part, str):
                        texts.append(part)

                out: dict = {"role": role, "content": "\n".join(texts)}
                if images:
                    out["images"] = images
                converted.append(out)
            else:
                converted.append({"role": role, "content": str(content)})

        return converted
