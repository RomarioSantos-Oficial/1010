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
                    id TEXT PRIMARY KEY, display_name TEXT,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                    content TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_messages_user ON messages(user_id, id);
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    memory_type TEXT NOT NULL, content TEXT NOT NULL,
                    canonical_key TEXT, confidence REAL NOT NULL DEFAULT 0.8,
                    importance REAL NOT NULL DEFAULT 0.5, created_at TEXT NOT NULL,
                    updated_at TEXT, last_used_at TEXT,
                    usage_count INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(user_id, memory_type, content)
                );
            """)
            self._migrate_memories(db)
            db.execute("CREATE INDEX IF NOT EXISTS ix_memories_user_active ON memories(user_id,active,importance)")

    def _migrate_memories(self, db: sqlite3.Connection) -> None:
        columns = {row["name"] for row in db.execute("PRAGMA table_info(memories)")}
        additions = {
            "canonical_key": "TEXT", "confidence": "REAL NOT NULL DEFAULT 0.8",
            "updated_at": "TEXT", "last_used_at": "TEXT",
            "usage_count": "INTEGER NOT NULL DEFAULT 0", "active": "INTEGER NOT NULL DEFAULT 1",
        }
        for name, declaration in additions.items():
            if name not in columns:
                db.execute(f"ALTER TABLE memories ADD COLUMN {name} {declaration}")
        db.execute("UPDATE memories SET canonical_key=memory_type || ':' || id WHERE canonical_key IS NULL")
        db.execute("UPDATE memories SET updated_at=created_at WHERE updated_at IS NULL")

    def _ensure_user(self, db: sqlite3.Connection, user_id: str) -> None:
        now = utc_now()
        db.execute(
            "INSERT INTO users(id,created_at,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at", (user_id, now, now),
        )

    def add_message(self, user_id: str, role: str, content: str) -> None:
        with self.connect() as db:
            self._ensure_user(db, user_id)
            db.execute("INSERT INTO messages(user_id,role,content,created_at) VALUES(?,?,?,?)", (user_id, role, content, utc_now()))

    def history(self, user_id: str, limit: int = 16) -> list[Message]:
        with self.connect() as db:
            rows = db.execute("SELECT role,content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    def add_memory(self, user_id: str, memory_type: str, content: str, importance: float = 0.6, canonical_key: str | None = None, confidence: float = 0.8) -> int:
        with self.connect() as db:
            self._ensure_user(db, user_id)
            now = utc_now()
            cursor = db.execute(
                "INSERT INTO memories(user_id,memory_type,content,canonical_key,confidence,importance,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                (user_id, memory_type, content, canonical_key or f"{memory_type}:{content}", confidence, importance, now, now),
            )
            return int(cursor.lastrowid)

    def find_by_canonical_key(self, user_id: str, canonical_key: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM memories WHERE user_id=? AND canonical_key=? AND active=1 ORDER BY id DESC LIMIT 1", (user_id, canonical_key)).fetchone()
        return dict(row) if row else None

    def update_memory(self, memory_id: int, content: str, confidence: float, importance: float, canonical_key: str | None = None) -> None:
        with self.connect() as db:
            db.execute(
                "UPDATE memories SET content=?,confidence=?,importance=?,canonical_key=COALESCE(?,canonical_key),updated_at=?,active=1 WHERE id=?",
                (content, confidence, importance, canonical_key, utc_now(), memory_id),
            )

    def touch_memories(self, memory_ids: list[int]) -> None:
        if not memory_ids:
            return
        placeholders = ",".join("?" for _ in memory_ids)
        with self.connect() as db:
            db.execute(f"UPDATE memories SET last_used_at=?,usage_count=usage_count+1 WHERE id IN ({placeholders})", (utc_now(), *memory_ids))

    def memories(self, user_id: str, limit: int = 20) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT id,user_id,memory_type,content,canonical_key,confidence,importance,created_at,updated_at,last_used_at,usage_count,active "
                "FROM memories WHERE user_id=? AND active=1 ORDER BY importance DESC,updated_at DESC LIMIT ?", (user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def all_active_memories(self) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM memories WHERE active=1 ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def clear_user(self, user_id: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM users WHERE id=?", (user_id,))

    def health(self) -> bool:
        with self.connect() as db:
            return db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
