"""
LLM Provider abstraction layer.

All providers implement the same `chat()` interface, returning a structured
`LLMResponse` so the agent loop can uniformly handle text replies and tool calls
regardless of whether the backend is Ollama, OpenAI, Anthropic, or Gemini.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """A single tool invocation requested by the LLM."""
    id: str            # provider-assigned ID (needed for multi-turn)
    name: str          # tool function name
    arguments: dict    # parsed arguments


@dataclass
class LLMResponse:
    """Structured response from any LLM provider."""
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None  # provider-specific raw response for debugging

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        """
        Send a conversation to the LLM and get a structured response.

        :param messages: Chat history in OpenAI-format dicts:
            [{"role": "system"|"user"|"assistant"|"tool", "content": ...}, ...]
            Image content is passed as a list within "content" (provider adapts).
        :param tools: Optional list of tool schemas (OpenAI function-calling format).
        :return: LLMResponse with either text or tool_calls populated.
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""
        ...
