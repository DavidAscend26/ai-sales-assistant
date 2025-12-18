from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings

async def get_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(url=settings.QDRANT_URL)

async def ensure_collection(client: AsyncQdrantClient, dim: int) -> None:
    collections = await client.get_collections()
    names = {c.name for c in collections.collections}
    if settings.QDRANT_COLLECTION not in names:
        await client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

async def upsert_points(client: AsyncQdrantClient, points: list[PointStruct]) -> None:
    await client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)