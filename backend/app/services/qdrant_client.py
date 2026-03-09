import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantConnector:
    def __init__(self):
        self._client = None
        self.collection_name = "community_summaries"
        self.vector_size = 384

    async def connect(self):
        try:
            self._client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
            collections = await self._client.get_collections()
            logger.info("Connected to Qdrant.")

            exists = any(c.name == self.collection_name for c in collections.collections)
            if not exists:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                await self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
                )
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self._client = None

    async def close(self):
        if self._client:
            self._client = None
            logger.info("Qdrant connection closed.")

    async def insert_summary(self, community_id: str, summary_text: str, vector: list[float], metadata: dict = None):
        """Embed summary and store in Qdrant."""
        if not self._client:
            logger.warning("Qdrant client not initialized, skipping insert.")
            return

        payload = {"text": summary_text}
        if metadata:
            payload.update(metadata)

        point = models.PointStruct(id=community_id, vector=vector, payload=payload)

        try:
            await self._client.upsert(collection_name=self.collection_name, wait=True, points=[point])
            logger.info(f"Inserted summary for community {community_id} into Qdrant.")
        except Exception as e:
            logger.error(f"Error inserting into Qdrant: {e}")


qdrant_client = QdrantConnector()
