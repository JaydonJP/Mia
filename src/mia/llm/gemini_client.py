"""
Google Gemini LLM client.

Translates between the OpenAI-style message/tool format used internally
by Mia and Gemini's native ``google-genai`` SDK format.
"""

from __future__ import annotations

import os
import json
import uuid
from .base import LLMProvider, LLMResponse, ToolCall


class GeminiClient(LLMProvider):
    def __init__(self, model: str = "gemini-2.0-flash"):
        self._model = model
        self.client = None

        from dotenv import load_dotenv
        secrets_path = os.path.expanduser("~/.mia/secrets.env")
        if os.path.exists(secrets_path):
            load_dotenv(secrets_path)

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("[Gemini] Warning: GEMINI_API_KEY not found. Set it in ~/.mia/secrets.env")
        else:
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key)
            except ImportError:
                print("[Gemini] Warning: google-genai package not installed.")

    @property
    def model_name(self) -> str:
        return f"Gemini ({self._model})"

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        if not self.client:
            return LLMResponse(
                text="Gemini client not configured. Set GEMINI_API_KEY in ~/.mia/secrets.env"
            )

        try:
            from google.genai import types
        except ImportError:
            return LLMResponse(text="[Gemini] google-genai package not installed.")

        # --- Extract system instruction ---
        system_instruction = None
        contents = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_instruction = content if isinstance(content, str) else str(content)
                continue

            # Map OpenAI roles to Gemini roles
            gemini_role = "model" if role == "assistant" else "user"

            if role == "tool":
                # Tool results go as a function response part
                tool_call_id = msg.get("tool_call_id", "")
                tool_name = msg.get("name", tool_call_id)
                try:
                    result_data = json.loads(content) if isinstance(content, str) else content
                except (json.JSONDecodeError, TypeError):
                    result_data = {"result": str(content)}
                if not isinstance(result_data, dict):
                    result_data = {"result": str(result_data)}

                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(
                        name=tool_name,
                        response=result_data,
                    )],
                ))
                continue

            # Handle multimodal content
            if isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            parts.append(types.Part.from_text(text=part["text"]))
                        elif part.get("type") == "image_url":
                            url = part.get("image_url", {}).get("url", "")
                            if url.startswith("data:"):
                                import base64
                                media_type = url.split(";")[0].split(":")[1]
                                b64_data = url.split(",", 1)[-1]
                                img_bytes = base64.b64decode(b64_data)
                                parts.append(types.Part.from_bytes(
                                    data=img_bytes,
                                    mime_type=media_type,
                                ))
                    elif isinstance(part, str):
                        parts.append(types.Part.from_text(text=part))
                contents.append(types.Content(role=gemini_role, parts=parts))
            elif role == "assistant" and msg.get("tool_calls"):
                # Reconstruct function call parts for the model's previous turn
                parts = []
                if content:
                    parts.append(types.Part.from_text(text=str(content)))
                for tc in msg["tool_calls"]:
                    fn = tc.get("function", {})
                    fn_args = fn.get("arguments", {})
                    if isinstance(fn_args, str):
                        try:
                            fn_args = json.loads(fn_args)
                        except json.JSONDecodeError:
                            fn_args = {}
                    parts.append(types.Part.from_function_call(
                        name=fn["name"],
                        args=fn_args,
                    ))
                contents.append(types.Content(role="model", parts=parts))
            else:
                contents.append(types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=str(content))],
                ))

        # --- Convert tools to Gemini function declarations ---
        gemini_tools = None
        if tools:
            func_declarations = []
            for t in tools:
                fn = t.get("function", {})
                params = fn.get("parameters", {})
                # Gemini doesn't accept 'required' inside properties
                schema = {
                    "type": "OBJECT",
                    "properties": {},
                }
                for prop_name, prop_def in params.get("properties", {}).items():
                    gtype = prop_def.get("type", "string").upper()
                    if gtype == "INTEGER":
                        gtype = "NUMBER"
                    schema["properties"][prop_name] = {
                        "type": gtype,
                        "description": prop_def.get("description", ""),
                    }
                if params.get("required"):
                    schema["required"] = params["required"]

                func_declarations.append(types.FunctionDeclaration(
                    name=fn["name"],
                    description=fn.get("description", ""),
                    parameters=schema,
                ))
            gemini_tools = [types.Tool(function_declarations=func_declarations)]

        # --- API call ---
        config_kwargs: dict = {}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        try:
            generate_kwargs: dict = {
                "model": self._model,
                "contents": contents,
            }
            config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None
            if gemini_tools:
                if config:
                    config.tools = gemini_tools
                else:
                    config = types.GenerateContentConfig(tools=gemini_tools)
            if config:
                generate_kwargs["config"] = config

            response = self.client.models.generate_content(**generate_kwargs)

            # --- Parse response ---
            text_parts = []
            tool_calls = []

            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        text_parts.append(part.text)
                    elif part.function_call:
                        fc = part.function_call
                        args = dict(fc.args) if fc.args else {}
                        tool_calls.append(ToolCall(
                            id=str(uuid.uuid4())[:8],
                            name=fc.name,
                            arguments=args,
                        ))

            return LLMResponse(
                text="\n".join(text_parts) if text_parts else None,
                tool_calls=tool_calls,
                raw=response,
            )

        except Exception as e:
            return LLMResponse(text=f"[Gemini error] {e}")
