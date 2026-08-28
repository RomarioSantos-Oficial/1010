from pathlib import Path

from qdrant_client import QdrantClient, models


class QdrantMemoryStore:
    collection = "luna_memories"

    def __init__(self, path: Path, vector_size: int):
        path.mkdir(parents=True, exist_ok=True)
        self.client = QdrantClient(path=str(path))
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )

    def upsert(self, memory_id: int, user_id: str, vector: list[float], payload: dict) -> None:
        self.client.upsert(
            self.collection,
            points=[models.PointStruct(id=memory_id, vector=vector, payload={**payload, "user_id": user_id})],
            wait=True,
        )

    def search(self, user_id: str, vector: list[float], limit: int = 6, score_threshold: float | None = None):
        result = self.client.query_points(
            collection_name=self.collection,
            query=vector,
            query_filter=models.Filter(
                must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
            ),
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )
        return result.points

    def delete_user(self, user_id: str) -> None:
        self.client.delete(
            self.collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
                )
            ),
            wait=True,
        )

    def close(self) -> None:
        self.client.close()
