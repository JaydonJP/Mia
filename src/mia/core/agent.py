"""
Mia Agent — the brain that orchestrates LLM reasoning and tool execution.

Implements a ReAct-style multi-turn tool loop:
  1. Build messages (system + history + user input)
  2. Send to LLM with tool schemas
  3. If LLM returns tool calls → execute → append results → loop back to 2
  4. If LLM returns text → final response → done
  5. Cap at max_steps to prevent runaway loops
"""

from __future__ import annotations

import json
import time
import threading
from collections import deque
from datetime import datetime

from .prompts import build_system_prompt
from .memory import SessionMemory
from .database import MiaDatabase
from ..actions.executor import setup_executor
from ..llm.router import LLMRouter
from ..llm.base import LLMResponse
from ..perception.screen import ScreenCapture
from ..perception.accessibility import AccessibilityTree
from ..privacy.redaction import Redactor


# ------------------------------------------------------------------
# Event log (for SSE / web UI — unchanged from original)
# ------------------------------------------------------------------

class EventLog:
    """Thread-safe event log for the UI to consume via SSE."""

    def __init__(self, max_events: int = 200):
        self.events: deque = deque(maxlen=max_events)
        self.listeners: list = []
        self._lock = threading.Lock()

    def emit(self, event_type: str, data: dict) -> None:
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        with self._lock:
            self.events.append(event)
            for callback in self.listeners:
                try:
                    callback(event)
                except Exception:
                    pass

    def subscribe(self, callback) -> None:
        with self._lock:
            self.listeners.append(callback)

    def unsubscribe(self, callback) -> None:
        with self._lock:
            if callback in self.listeners:
                self.listeners.remove(callback)

    def get_recent(self, n: int = 50) -> list[dict]:
        with self._lock:
            return list(self.events)[-n:]


# ------------------------------------------------------------------
# Agent
# ------------------------------------------------------------------

MAX_TOOL_STEPS = 10  # Safety cap for the ReAct loop


class Agent:
    def __init__(self, config: dict):
        self.config = config
        self.db = MiaDatabase()
        self.memory = SessionMemory(database=self.db)
        self.executor = setup_executor()
        self.router = LLMRouter(config)
        self.screen = ScreenCapture()
        self.a11y = AccessibilityTree()
        self.redactor = Redactor()
        self.event_log = EventLog()
        self.state: str = "idle"

        # Console callback — set by the CLI to display logs
        self.on_log = None  # Callable[[str, str], None]  (category, message)

    # ------------------------------------------------------------------
    # Internal logging
    # ------------------------------------------------------------------
    def _log(self, category: str, message: str) -> None:
        """Log a message to the event log and optional console callback."""
        self.event_log.emit("activity", {"category": category, "message": message})
        if self.on_log:
            self.on_log(category, message)

    def _set_state(self, new_state: str) -> None:
        self.state = new_state
        self.event_log.emit("state_change", {"state": new_state})

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def process(self, user_text: str, tts_engine=None) -> str:
        """
        Process a user request through the full ReAct loop.

        Returns the final text response from Mia.
        """
        self._set_state("thinking")
        self.memory.add_user(user_text)
        self.event_log.emit("user_message", {"text": user_text})

        # 1. Build the system prompt with dynamic context
        user_profile = self.db.get_all_profile()
        system_prompt = build_system_prompt(
            provider=self.router.mode,
            model=self.router.get_model_name(),
            user_profile=user_profile if user_profile else None,
        )

        # 2. Build message history for the LLM
        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
        ]

        # Add conversation history (previous turns)
        for msg in self.memory.get_messages()[:-1]:  # Exclude the user msg we just added
            if msg["role"] in ("user", "assistant"):
                messages.append(msg)

        # Add current user message
        messages.append({"role": "user", "content": user_text})

        # 3. ReAct loop
        tool_schemas = self.executor.get_schemas()
        final_response = ""
        step = 0

        while step < MAX_TOOL_STEPS:
            step += 1
            self._log("LLM", f"Sending to {self.router.get_model_name()} (step {step})...")
            self._set_state("thinking")

            # Call the LLM
            llm_response: LLMResponse = self.router.chat(messages, tools=tool_schemas)

            # --- LLM returned tool calls → execute them ---
            if llm_response.has_tool_calls:
                self._set_state("acting")

                # Build the assistant message with tool calls for history
                assistant_msg: dict = {
                    "role": "assistant",
                    "content": llm_response.text or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in llm_response.tool_calls
                    ],
                }
                messages.append(assistant_msg)

                # Execute each tool call and feed results back
                for tc in llm_response.tool_calls:
                    self._log("Tool", f"Executing: {tc.name}({json.dumps(tc.arguments)})")
                    self.event_log.emit("tool_call", {"tool": tc.name, "args": tc.arguments})

                    result = self.executor.execute(tc.name, tc.arguments)

                    self._log("Tool", f"Result: {result[:200]}")
                    self.event_log.emit("tool_result", {"tool": tc.name, "result": str(result)[:500]})

                    # Log to persistent DB
                    self.db.log_action(
                        tool_name=tc.name,
                        arguments=tc.arguments,
                        result=result,
                        success="error" not in result.lower() and "failed" not in result.lower(),
                    )

                    # If this is the `respond` tool, capture as the spoken output
                    if tc.name == "respond":
                        spoken_text = tc.arguments.get("text", result)
                        final_response = spoken_text
                        self._set_state("speaking")
                        if tts_engine:
                            tts_engine.speak(spoken_text)
                        self.event_log.emit("mia_response", {"text": spoken_text})

                    # Add tool result to messages for the next LLM turn
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.name,
                        "content": result,
                    })

                # If the LLM only called `respond`, we're done
                if all(tc.name == "respond" for tc in llm_response.tool_calls):
                    break

                # Otherwise, loop back so the LLM can see tool results and decide next step
                continue

            # --- LLM returned plain text (no tool calls) → final response ---
            else:
                text = llm_response.text or ""
                if text:
                    final_response = text
                    self._set_state("speaking")
                    if tts_engine:
                        tts_engine.speak(text)
                    self.event_log.emit("mia_response", {"text": text})
                break

        # Fallback if loop exhausted
        if not final_response:
            final_response = "I completed the actions but have nothing more to say."
            self.event_log.emit("mia_response", {"text": final_response})

        self.memory.add_assistant(final_response)
        self._set_state("idle")
        return final_response
