import hashlib
import re
from collections.abc import Sequence

from memory.embeddings import EmbeddingProvider
from memory.memory_candidate import normalize
from memory.qdrant_store import QdrantMemoryStore
from memory.semantic_memory import SemanticMemory
from memory.service import MemoryService
from memory.sqlite_store import SQLiteStore


class TestEmbeddings(EmbeddingProvider):
    """Embedding determinístico pequeno, reservado aos testes."""

    @property
    def dimension(self) -> int:
        return 32

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        result = []
        synonyms = {"discretos": "discreto", "discretas": "discreto", "chamativos": "marcante", "vestidos": "vestido", "pretos": "preto"}
        for text in texts:
            vector = [0.0] * self.dimension
            for token in re.findall(r"\w+", normalize(text)):
                token = synonyms.get(token, token)
                vector[int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dimension] += 1.0
            norm = sum(value * value for value in vector) ** 0.5 or 1
            result.append([value / norm for value in vector])
        return result


def make_memory(tmp_path):
    sqlite = SQLiteStore(tmp_path / "app.db")
    embeddings = TestEmbeddings()
    vectors = QdrantMemoryStore(tmp_path / "qdrant", embeddings.dimension)
    semantic = SemanticMemory(sqlite, vectors, embeddings, similarity_threshold=0.80)
    return sqlite, semantic, MemoryService(sqlite, semantic)

