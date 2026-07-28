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
        from ollama import Client
        client = Client(host="http://127.0.0.1:11434")

        # Ollama expects its own message format — mostly OpenAI-compatible
        # but images go in a top-level "images" key per message.
        ollama_messages = self._convert_messages(messages)

        kwargs: dict = {}
        if tools:
            kwargs["tools"] = tools

        try:
            try:
                response = client.chat(
                    model=self._model,
                    messages=ollama_messages,
                    **kwargs,
                )
            except Exception as e:
                if "does not support tools" in str(e) and tools:
                    # Model doesn't support native tool calling — retry without tools
                    kwargs.pop("tools", None)
                    
                    tool_instructions = (
                        "CRITICAL INSTRUCTION: You are an AI assistant that uses tools to perform actions.\n"
                        "You have access to the following tools:\n"
                        + json.dumps([t["function"] for t in tools], indent=2) + "\n\n"
                        "To use a tool, you MUST output EXACTLY this XML format:\n"
                        "<tool_call>{\"name\": \"tool_name\", \"arguments\": {\"arg_name\": \"value\"}}</tool_call>\n\n"
                        "Do not just say 'Opening app'. You MUST output the <tool_call> tag to actually perform the action!"
                    )
                    
                    modified_messages = list(ollama_messages)
                    has_system = False
                    for i, m in enumerate(modified_messages):
                        if m.get("role") == "system":
                            modified_messages[i] = {"role": "system", "content": m.get("content", "") + "\n\n" + tool_instructions}
                            has_system = True
                            break
                    if not has_system:
                        modified_messages.insert(0, {"role": "system", "content": tool_instructions})
                        
                    # print("DEBUG OLLAMA MESSAGES:", json.dumps(modified_messages, indent=2))

                    response = client.chat(
                        model=self._model,
                        messages=modified_messages,
                        **kwargs,
                    )
                else:
                    raise

            message = response.get("message", {})

            # --- Native Tool calls ---
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

            # --- Plain text or Manual Tool Calls ---
            content = message.get("content", "")
            
            import re
            pattern = r"<tool_call>\s*(\{.*?\})(?:\s*</tool_call>|$)"
            matches = list(re.finditer(pattern, content, re.DOTALL))
            
            if matches:
                manual_tool_calls = []
                for match in matches:
                    try:
                        tc_data = json.loads(match.group(1))
                        manual_tool_calls.append(ToolCall(
                            id=str(uuid.uuid4())[:8],
                            name=tc_data.get("name", ""),
                            arguments=tc_data.get("arguments", {}),
                        ))
                    except json.JSONDecodeError:
                        pass
                
                clean_text = re.sub(pattern, "", content, flags=re.DOTALL).strip()
                return LLMResponse(text=clean_text or None, tool_calls=manual_tool_calls, raw=response)

            return LLMResponse(text=content, raw=response)

        except Exception as e:
            raise RuntimeError(f"[Ollama error] {e}") from e

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
