import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantConnector:
    def __init__(self):
        self._client = None
        self.collection_name = "community_summaries"
        self.raptor_collection_name = "raptor_trees"
        self.vector_size = 384

    async def connect(self):
        try:
            self._client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
            collections = await self._client.get_collections()
            logger.info("Connected to Qdrant.")

            # Create community summaries collection if not exists
            exists = any(c.name == self.collection_name for c in collections.collections)
            if not exists:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                await self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
                )
            
            # Create RAPTOR trees collection if not exists  
            raptor_exists = any(c.name == self.raptor_collection_name for c in collections.collections)
            if not raptor_exists:
                logger.info(f"Creating Qdrant collection: {self.raptor_collection_name}")
                await self._client.create_collection(
                    collection_name=self.raptor_collection_name,
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

    async def insert_raptor_nodes(self, nodes: list[dict]):
        """
        Insert RAPTOR tree nodes into Qdrant for persistent storage and retrieval.
        Each node dict should contain: node_id, text, embedding, level, metadata.
        """
        if not self._client:
            logger.warning("Qdrant client not initialized, skipping RAPTOR insert.")
            return

        points = []
        for node_data in nodes:
            point = models.PointStruct(
                id=node_data["node_id"],
                vector=node_data["embedding"],
                payload={
                    "text": node_data["text"],
                    "level": node_data["level"],
                    "parent_id": node_data.get("parent_id"),
                    "children": node_data.get("children", []),
                    "metadata": node_data.get("metadata", {}),
                },
            )
            points.append(point)

        try:
            await self._client.upsert(
                collection_name=self.raptor_collection_name, wait=True, points=points
            )
            logger.info(f"Inserted {len(points)} RAPTOR nodes into Qdrant.")
        except Exception as e:
            logger.error(f"Error inserting RAPTOR nodes into Qdrant: {e}")

    async def search_raptor_nodes(
        self, query_vector: list[float], document_name: str, top_k: int = 5, level_filter: list[int] = None
    ) -> list[dict]:
        """
        Search RAPTOR tree nodes in Qdrant by similarity to query.
        Optionally filter by document name and tree levels.
        """
        if not self._client:
            logger.warning("Qdrant client not initialized, skipping search.")
            return []

        # Build filter conditions
        filter_conditions = [
            models.FieldCondition(
                key="metadata.document", match=models.MatchValue(value=document_name)
            )
        ]
        
        if level_filter:
            filter_conditions.append(
                models.FieldCondition(
                    key="level", match=models.MatchAny(any=level_filter)
                )
            )

        try:
            results = await self._client.search(
                collection_name=self.raptor_collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=models.Filter(must=filter_conditions) if filter_conditions else None,
            )

            return [
                {
                    "node_id": hit.id,
                    "text": hit.payload.get("text", ""),
                    "level": hit.payload.get("level", 0),
                    "similarity": hit.score,
                    "metadata": hit.payload.get("metadata", {}),
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Error searching RAPTOR nodes in Qdrant: {e}")
            return []


qdrant_client = QdrantConnector()
