from .embeddings import EmbeddingProvider
from .qdrant_store import QdrantMemoryStore
from .schemas import MemoryCandidate
from .sqlite_store import SQLiteStore


class SemanticMemory:
    def __init__(self, sqlite: SQLiteStore, vectors: QdrantMemoryStore, embeddings: EmbeddingProvider, similarity_threshold: float = 0.88):
        self.sqlite = sqlite
        self.vectors = vectors
        self.embeddings = embeddings
        self.similarity_threshold = similarity_threshold

    def sync_existing(self) -> int:
        records = self.sqlite.all_active_memories()
        if not records:
            return 0
        vectors = self.embeddings.encode([record["content"] for record in records])
        for record, vector in zip(records, vectors, strict=True):
            self.vectors.upsert(record["id"], record["user_id"], vector, {
                "content": record["content"], "memory_type": record["memory_type"],
                "canonical_key": record["canonical_key"], "confidence": record["confidence"],
                "importance": record["importance"],
            })
        return len(records)

    def remember(self, user_id: str, candidate: MemoryCandidate) -> tuple[int, str]:
        vector = self.embeddings.encode([candidate.content])[0]
        exact = self.sqlite.find_by_canonical_key(user_id, candidate.canonical_key)
        if exact:
            memory_id, operation = exact["id"], "updated"
            self.sqlite.update_memory(memory_id, candidate.content, candidate.confidence, candidate.importance, candidate.canonical_key)
        else:
            similar = self.vectors.search(user_id, vector, 1, self.similarity_threshold)
            if similar:
                memory_id, operation = int(similar[0].id), "deduplicated"
                payload = similar[0].payload or {}
                self.sqlite.update_memory(memory_id, candidate.content, max(candidate.confidence, float(payload.get("confidence", 0))), max(candidate.importance, float(payload.get("importance", 0))), candidate.canonical_key)
            else:
                memory_id, operation = self.sqlite.add_memory(user_id, candidate.memory_type, candidate.content, candidate.importance, candidate.canonical_key, candidate.confidence), "created"
        self.vectors.upsert(memory_id, user_id, vector, {
            "content": candidate.content, "memory_type": candidate.memory_type,
            "canonical_key": candidate.canonical_key, "confidence": candidate.confidence,
            "importance": candidate.importance,
        })
        return memory_id, operation

    def retrieve(self, user_id: str, query: str, limit: int = 6) -> list[str]:
        points = self.vectors.search(user_id, self.embeddings.encode([query])[0], limit)
        self.sqlite.touch_memories([int(point.id) for point in points])
        return [str((point.payload or {}).get("content", "")) for point in points]

    def delete_user(self, user_id: str) -> None:
        self.vectors.delete_user(user_id)
        self.sqlite.clear_user(user_id)

    def close(self) -> None:
        self.vectors.close()
