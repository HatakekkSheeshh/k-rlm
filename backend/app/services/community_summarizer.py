"""
Community summarization pipeline: Communities → LLM → Embedding → Qdrant.
"""
import hashlib
import logging
from typing import Optional

from app.ollama_client import generate, get_embedding
from app.services.neo4j_client import Community
from app.services.qdrant_client import qdrant_client

logger = logging.getLogger(__name__)


def _community_hash(community_id: int, document_name: str) -> str:
    """Generate a deterministic hash ID for Qdrant point."""
    raw = f"{document_name}::community::{community_id}"
    return hashlib.md5(raw.encode()).hexdigest()


async def summarize_community(community: Community, model: str = "phi3:mini") -> Optional[str]:
    """Generate summary of community context using LLM."""
    context = community.context_text()
    if not context.strip():
        return None

    prompt = (
        "You are a knowledge graph analyst. "
        "Summarize the following community of entities and their relationships "
        "into a concise paragraph. Focus on the key themes and connections.\n\n"
        f"{context}\n\n"
        "Summary:"
    )

    try:
        raw = await generate(prompt=prompt, model=model)
        summary = raw.get("output", "").strip()
        if summary:
            logger.info(f"Community {community.id}: summarized ({len(summary)} chars)")
        return summary or None
    except Exception as e:
        logger.error(f"Failed to summarize community {community.id}: {e}")
        return None


async def store_community_summary(community: Community, summary: str, document_name: str) -> bool:
    """Embed summary and store in Qdrant."""
    try:
        vector = await get_embedding(summary)
        point_id = _community_hash(community.id, document_name)
        metadata = {
            "document": document_name,
            "community_id": community.id,
            "node_count": len(community.nodes),
            "edge_count": len(community.edges),
            "node_ids": [n["id"] for n in community.nodes],
        }
        await qdrant_client.insert_summary(community_id=point_id, summary_text=summary, vector=vector, metadata=metadata)
        return True
    except Exception as e:
        logger.error(f"Failed to store community {community.id} in Qdrant: {e}")
        return False


async def run_community_pipeline(document_name: str, model: str = "phi3:mini") -> list[dict]:
    """Detect communities → summarize → store in Qdrant. Returns list of summaries."""
    from app.services.neo4j_client import neo4j_client

    logger.info(f"=== COMMUNITY PIPELINE START: {document_name} ===")

    communities = await neo4j_client.detect_communities(document_name)
    if not communities:
        logger.warning("No communities detected, skipping pipeline.")
        return []

    logger.info(f"Found {len(communities)} communities. Summarizing...")

    results = []
    for community in communities:
        summary = await summarize_community(community, model=model)
        if not summary:
            continue

        stored = await store_community_summary(community, summary, document_name)
        results.append({
            "community_id": community.id,
            "node_count": len(community.nodes),
            "edge_count": len(community.edges),
            "summary": summary,
            "stored_in_qdrant": stored,
        })

    logger.info(f"=== COMMUNITY PIPELINE DONE: {len(results)}/{len(communities)} summarized ===")
    return results
