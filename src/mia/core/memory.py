"""
Session memory — in-memory conversation context for the current session.

Also persists messages to the SQLite database so they survive restarts.
The in-memory list is what gets sent to the LLM; the DB is for
long-term recall and audit.
"""

from __future__ import annotations

import uuid
from datetime import datetime


class SessionMemory:
    def __init__(self, max_turns: int = 20, database=None):
        self.history: list[dict] = []
        self.max_turns = max_turns
        self.session_id: str = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
        self._db = database  # Optional MiaDatabase instance

    def add_user(self, text: str) -> None:
        self.history.append({"role": "user", "content": text})
        self._trim()
        if self._db:
            self._db.log_message(self.session_id, "user", text)

    def add_assistant(self, text: str) -> None:
        self.history.append({"role": "assistant", "content": text})
        self._trim()
        if self._db:
            self._db.log_message(self.session_id, "assistant", text)

    def add_system(self, text: str) -> None:
        """Log system events (tool results, verification notes, etc.)."""
        self.history.append({"role": "system", "content": text})
        self._trim()

    def _trim(self) -> None:
        max_messages = self.max_turns * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def get_context(self) -> str:
        if not self.history:
            return "No previous conversation."
        return "\n".join(f"{msg['role']}: {msg['content']}" for msg in self.history)

    def get_messages(self) -> list[dict]:
        """Return structured message list for the LLM API."""
        return list(self.history)

    def get_history_list(self) -> list[dict]:
        """Return structured history for API endpoints."""
        return list(self.history)

    def clear(self) -> None:
        self.history = []

    def load_from_db(self, n: int = 10) -> None:
        """Bootstrap session memory with recent messages from the database."""
        if not self._db:
            return
        recent = self._db.get_recent_messages(n)
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant"):
                self.history.append({"role": role, "content": content})
        self._trim()
