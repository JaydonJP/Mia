"""
Persistent database — SQLite-backed storage for conversations,
action logs, and user profile data.

Uses Python's built-in ``sqlite3`` module for zero-dependency persistence.
DB file lives at ``~/.mia/mia.db``.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path


_DB_PATH = os.path.expanduser(os.environ.get("MIA_DB_PATH", "~/.mia/mia.db"))
_PROJECT_FALLBACK_DB_PATH = Path(__file__).resolve().parents[3] / "logs" / "mia.db"


class MiaDatabase:
    """Thread-safe SQLite database for Mia's persistent state."""

    def __init__(self, db_path: str | None = None):
        self.db_path = os.path.expandvars(os.path.expanduser(db_path or _DB_PATH))
        self.disabled = False
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        try:
            self._init_tables()
            self._assert_writable()
        except sqlite3.Error:
            self._close_current_connection()
            fallback = str(_PROJECT_FALLBACK_DB_PATH)
            if os.path.realpath(self.db_path) != os.path.realpath(fallback):
                self.db_path = fallback
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
                try:
                    self._init_tables()
                    self._assert_writable()
                    return
                except sqlite3.Error:
                    self._close_current_connection()
            self.disabled = True

    @property
    def _conn(self) -> sqlite3.Connection:
        """One connection per thread (SQLite requirement)."""
        if self.disabled:
            raise sqlite3.OperationalError("Mia database is disabled")
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    def _close_current_connection(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            try:
                conn.close()
            except sqlite3.Error:
                pass
            self._local.conn = None

    def close(self) -> None:
        """Close the current thread's SQLite connection."""
        self._close_current_connection()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _assert_writable(self) -> None:
        self._conn.execute("CREATE TABLE IF NOT EXISTS _mia_write_probe (id INTEGER)")
        self._conn.execute("INSERT INTO _mia_write_probe (id) VALUES (1)")
        self._conn.execute("DELETE FROM _mia_write_probe")
        self._conn.commit()

    def _init_tables(self):
        conn = self._conn
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                timestamp   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS action_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name   TEXT NOT NULL,
                arguments   TEXT,
                result      TEXT,
                success     INTEGER DEFAULT 1,
                timestamp   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_profile (
                key         TEXT PRIMARY KEY,
                value       TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_conv_session
                ON conversations(session_id);
            CREATE INDEX IF NOT EXISTS idx_conv_timestamp
                ON conversations(timestamp);
            CREATE INDEX IF NOT EXISTS idx_action_timestamp
                ON action_log(timestamp);
        """)
        conn.commit()

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------
    def log_message(self, session_id: str, role: str, content: str) -> None:
        if self.disabled:
            return
        try:
            self._conn.execute(
                "INSERT INTO conversations (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, role, content, datetime.now().isoformat()),
            )
            self._conn.commit()
        except sqlite3.Error:
            self.disabled = True

    def get_recent_messages(self, n: int = 20) -> list[dict]:
        """Get the N most recent messages across all sessions."""
        if self.disabled:
            return []
        rows = self._conn.execute(
            "SELECT session_id, role, content, timestamp FROM conversations ORDER BY id DESC LIMIT ?",
            (n,),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_session_messages(self, session_id: str) -> list[dict]:
        if self.disabled:
            return []
        rows = self._conn.execute(
            "SELECT role, content, timestamp FROM conversations WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Action log
    # ------------------------------------------------------------------
    def log_action(
        self,
        tool_name: str,
        arguments: dict | str,
        result: str,
        success: bool = True,
    ) -> None:
        if self.disabled:
            return
        args_str = json.dumps(arguments) if isinstance(arguments, dict) else str(arguments)
        try:
            self._conn.execute(
                "INSERT INTO action_log (tool_name, arguments, result, success, timestamp) VALUES (?, ?, ?, ?, ?)",
                (tool_name, args_str, result[:2000], int(success), datetime.now().isoformat()),
            )
            self._conn.commit()
        except sqlite3.Error:
            self.disabled = True

    def get_recent_actions(self, n: int = 20) -> list[dict]:
        if self.disabled:
            return []
        rows = self._conn.execute(
            "SELECT tool_name, arguments, result, success, timestamp FROM action_log ORDER BY id DESC LIMIT ?",
            (n,),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    # ------------------------------------------------------------------
    # User profile
    # ------------------------------------------------------------------
    def set_profile(self, key: str, value: str) -> None:
        if self.disabled:
            return
        try:
            self._conn.execute(
                "INSERT OR REPLACE INTO user_profile (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now().isoformat()),
            )
            self._conn.commit()
        except sqlite3.Error:
            self.disabled = True

    def get_profile(self, key: str) -> str | None:
        if self.disabled:
            return None
        row = self._conn.execute(
            "SELECT value FROM user_profile WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def get_all_profile(self) -> dict[str, str]:
        if self.disabled:
            return {}
        rows = self._conn.execute("SELECT key, value FROM user_profile").fetchall()
        return {r["key"]: r["value"] for r in rows}

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search_history(self, query: str, limit: int = 10) -> list[dict]:
        """Full-text search across conversation content."""
        if self.disabled:
            return []
        rows = self._conn.execute(
            "SELECT session_id, role, content, timestamp FROM conversations WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]
