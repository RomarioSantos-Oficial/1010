from .memory_candidate import MemoryCandidateExtractor
from .semantic_memory import SemanticMemory
from .sqlite_store import SQLiteStore


class MemoryService:
    def __init__(self, store: SQLiteStore, semantic: SemanticMemory, extractor: MemoryCandidateExtractor | None = None):
        self.store = store
        self.semantic = semantic
        self.extractor = extractor or MemoryCandidateExtractor()

    def observe(self, user_id: str, text: str) -> list[tuple[int, str]]:
        return [self.semantic.remember(user_id, candidate) for candidate in self.extractor.extract(text)]

    def retrieve(self, user_id: str, query: str, limit: int = 6) -> list[str]:
        return self.semantic.retrieve(user_id, query, limit)

    def clear_user(self, user_id: str) -> None:
        self.semantic.delete_user(user_id)

