import re

from .sqlite_store import SQLiteStore


class MemoryService:
    def __init__(self, store: SQLiteStore):
        self.store = store

    def observe(self, user_id: str, text: str) -> None:
        patterns = [
            (r"(?:eu )?(?:gosto|prefiro) de? (.+)", "preference"),
            (r"(?:me chamo|meu nome é) (.+)", "display_name"),
            (r"(?:responda|prefiro respostas) (mais curtas|curtas|mais detalhadas|detalhadas)", "response_style"),
        ]
        for pattern, kind in patterns:
            match = re.search(pattern, text.strip(), flags=re.IGNORECASE)
            if match:
                content = match.group(0).strip().rstrip(".!?")[:240]
                self.store.add_memory(user_id, kind, content, 0.8)
                break

