"""
Tool registry — stores tool schemas and their Python implementations.

Tool schemas follow the OpenAI function-calling format so they can be
sent directly to any provider (each client translates if needed).
"""

from __future__ import annotations

from typing import Callable


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Callable] = {}
        self.schemas: list[dict] = []

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        func: Callable,
    ) -> None:
        self.tools[name] = func

        # OpenAI function-calling schema
        self.schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameters.get("properties", {}),
                    "required": parameters.get("required", []),
                },
            },
        })

    def get_schemas(self) -> list[dict]:
        return self.schemas

    def execute(self, name: str, kwargs: dict) -> str:
        """Execute a registered tool and return the result as a string."""
        if name not in self.tools:
            return f"Tool '{name}' not found. Available: {', '.join(self.tools.keys())}"
        try:
            result = self.tools[name](**kwargs)
            return str(result) if result is not None else "Done."
        except TypeError as e:
            return f"Error calling {name}: bad arguments — {e}"
        except Exception as e:
            return f"Error executing {name}: {e}"

    def list_tools(self) -> list[str]:
        """Return a list of registered tool names."""
        return list(self.tools.keys())
