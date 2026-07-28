"""
LLM Router — picks the right provider based on the configured mode.

Modes:
  - local:  Always use Ollama (runs on machine).
  - cloud:  Always use the configured cloud provider (OpenAI/Anthropic/Gemini).
  - auto:   Simple heuristic — use local for quick tasks, cloud for complex ones.
"""

from __future__ import annotations

from .base import LLMProvider, LLMResponse
from .ollama_client import OllamaClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .gemini_client import GeminiClient


class LLMRouter:
    def __init__(self, config: dict):
        self.config = config.get("llm", {})
        self.mode: str = self.config.get("mode", "local")

        # --- Local client ---
        local_cfg = self.config.get("local", {})
        self.local_client: LLMProvider = OllamaClient(
            model=local_cfg.get("vision_model", "qwen2.5vl:7b"),
        )

        # --- Cloud client ---
        cloud_cfg = self.config.get("cloud", {})
        self.cloud_client: LLMProvider | None = self._build_cloud_client(cloud_cfg)

    @staticmethod
    def _build_cloud_client(cloud_cfg: dict) -> LLMProvider | None:
        provider = cloud_cfg.get("provider", "openai")
        model = cloud_cfg.get("model")

        if provider == "openai":
            return OpenAIClient(model=model or "gpt-4o")
        elif provider == "anthropic":
            return AnthropicClient(model=model or "claude-sonnet-4-20250514")
        elif provider == "gemini":
            return GeminiClient(model=model or "gemini-3.5-flash")
        return None

    # ------------------------------------------------------------------
    def set_mode(self, mode: str) -> None:
        self.mode = mode

    def set_cloud_provider(self, provider: str) -> None:
        cloud_cfg = self.config.setdefault("cloud", {})
        cloud_cfg["provider"] = provider
        self.cloud_client = self._build_cloud_client(cloud_cfg)

    def set_cloud_model(self, model: str) -> None:
        cloud_cfg = self.config.setdefault("cloud", {})
        cloud_cfg["model"] = model
        self.cloud_client = self._build_cloud_client(cloud_cfg)

    def get_active_provider(self) -> LLMProvider:
        """Return the provider that will handle the next request."""
        if self.mode == "cloud" and self.cloud_client:
            return self.cloud_client
        return self.local_client

    def get_model_name(self) -> str:
        return self.get_active_provider().model_name

    @staticmethod
    def _client_ready(client: LLMProvider | None) -> bool:
        if client is None:
            return False
        configured_client = getattr(client, "client", True)
        return configured_client is not None

    # ------------------------------------------------------------------
    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        """Route a chat request to the appropriate provider."""

        if self.mode == "cloud" and self.cloud_client:
            return self.cloud_client.chat(messages, tools)

        if self.mode == "auto":
            # Simple heuristic: if there are images in the messages or
            # the conversation is long (complex), prefer cloud.
            has_images = any(
                isinstance(m.get("content"), list)
                and any(
                    isinstance(p, dict) and p.get("type") == "image_url"
                    for p in m["content"]
                )
                for m in messages
            )
            is_complex = len(messages) > 8

            if (has_images or is_complex) and self._client_ready(self.cloud_client):
                return self.cloud_client.chat(messages, tools)

        # Default: local
        return self.local_client.chat(messages, tools)
