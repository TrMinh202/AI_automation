from qdrant_client import QdrantClient as _QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from app.config import settings


class QdrantClientWrapper:
    def __init__(self) -> None:
        self._client = _QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        self.collection_name = settings.qdrant_collection_name

    def ensure_collection(self) -> None:
        existing = {c.name for c in self._client.get_collections().collections}
        if self.collection_name not in existing:
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
            )

    def upsert(self, points: list[PointStruct]) -> None:
        self._client.upsert(collection_name=self.collection_name, points=points)

    def search(self, vector: list[float], limit: int = 5) -> list:
        result = self._client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
        )
        return result.points

    def scroll(self, limit: int = 10) -> list:
        result, _ = self._client.scroll(collection_name=self.collection_name, limit=limit)
        return result

    def is_healthy(self) -> bool:
        try:
            self._client.get_collections()
            return True
        except Exception:
            return False
