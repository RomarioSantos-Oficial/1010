import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from brain.llm_provider import Message


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    display_name TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_messages_user ON messages(user_id, id);
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance REAL NOT NULL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, memory_type, content)
                );
            """)

    def _ensure_user(self, db: sqlite3.Connection, user_id: str) -> None:
        now = utc_now()
        db.execute(
            "INSERT INTO users(id, created_at, updated_at) VALUES(?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at",
            (user_id, now, now),
        )

    def add_message(self, user_id: str, role: str, content: str) -> None:
        with self.connect() as db:
            self._ensure_user(db, user_id)
            db.execute(
                "INSERT INTO messages(user_id, role, content, created_at) VALUES(?,?,?,?)",
                (user_id, role, content, utc_now()),
            )

    def history(self, user_id: str, limit: int = 12) -> list[Message]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT role, content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    def add_memory(self, user_id: str, memory_type: str, content: str, importance: float = 0.6) -> None:
        with self.connect() as db:
            self._ensure_user(db, user_id)
            db.execute(
                "INSERT OR IGNORE INTO memories(user_id,memory_type,content,importance,created_at) "
                "VALUES(?,?,?,?,?)",
                (user_id, memory_type, content, importance, utc_now()),
            )

    def memories(self, user_id: str, limit: int = 20) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT id,memory_type,content,importance,created_at FROM memories "
                "WHERE user_id=? ORDER BY importance DESC,id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def retrieve(self, user_id: str, query: str, limit: int = 6) -> list[str]:
        items = self.memories(user_id, 50)
        terms = set(re.findall(r"\w+", query.casefold()))
        ranked = sorted(
            items,
            key=lambda item: (
                len(terms & set(re.findall(r"\w+", item["content"].casefold()))),
                item["importance"],
            ),
            reverse=True,
        )
        return [item["content"] for item in ranked[:limit]]

    def clear_user(self, user_id: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM users WHERE id=?", (user_id,))

