"""
RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval) Service.

Builds a hierarchical tree of document summaries at multiple abstraction levels:
- Level 0: Raw text chunks (leaf nodes)
- Level 1+: Clustered summaries (recursive abstraction)

At query time, retrieves relevant context from multiple tree levels
for comprehensive question answering.
"""

import logging
import hashlib
import numpy as np
from typing import Optional
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from app.ollama_client import generate, get_embedding

logger = logging.getLogger(__name__)


class RAPTORNode:
    """Represents a node in the RAPTOR tree."""
    
    def __init__(
        self,
        node_id: str,
        text: str,
        embedding: list[float],
        level: int,
        parent_id: Optional[str] = None,
        children: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ):
        self.node_id = node_id
        self.text = text
        self.embedding = embedding
        self.level = level
        self.parent_id = parent_id
        self.children = children or []
        self.metadata = metadata or {}


class RAPTORTree:
    """RAPTOR hierarchical tree builder and retriever."""
    
    def __init__(
        self,
        chunk_size: int = 400,
        max_clusters_per_level: int = 5,
        max_levels: int = 3,
        model: str = "phi3:mini",
    ):
        self.chunk_size = chunk_size
        self.max_clusters_per_level = max_clusters_per_level
        self.max_levels = max_levels
        self.model = model
        self.nodes: dict[str, RAPTORNode] = {}
    
    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks of approximately chunk_size words."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size):
            chunk = " ".join(words[i:i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks
    
    def _generate_node_id(self, text: str, level: int, index: int) -> str:
        """Generate deterministic node ID."""
        content = f"{text[:100]}::L{level}::I{index}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            try:
                embedding = await get_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to embed text: {e}")
                # Fallback: zero vector
                embeddings.append([0.0] * 384)
        return embeddings
    
    def _cluster_embeddings(
        self, embeddings: list[list[float]], min_clusters: int = 2
    ) -> tuple[np.ndarray, int]:
        """
        Cluster embeddings using K-means with automatic cluster selection.
        Returns cluster labels and optimal number of clusters.
        """
        embeddings_array = np.array(embeddings)
        n_samples = len(embeddings)
        
        # Can't cluster if too few samples
        if n_samples < min_clusters:
            return np.zeros(n_samples, dtype=int), 1
        
        # Try different numbers of clusters and pick best based on silhouette score
        max_k = min(self.max_clusters_per_level, n_samples - 1)
        if max_k < min_clusters:
            return np.zeros(n_samples, dtype=int), 1
        
        best_score = -1
        best_labels = None
        best_k = min_clusters
        
        for k in range(min_clusters, max_k + 1):
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings_array)
                
                # Silhouette score measures cluster quality (-1 to 1, higher is better)
                score = silhouette_score(embeddings_array, labels)
                
                if score > best_score:
                    best_score = score
                    best_labels = labels
                    best_k = k
            except Exception as e:
                logger.warning(f"Clustering with k={k} failed: {e}")
                continue
        
        if best_labels is None:
            # Fallback: single cluster
            return np.zeros(n_samples, dtype=int), 1
        
        logger.info(f"Selected {best_k} clusters with silhouette score: {best_score:.3f}")
        return best_labels, best_k
    
    async def _summarize_cluster(self, texts: list[str]) -> str:
        """Generate a summary of multiple related text chunks."""
        if len(texts) == 1:
            return texts[0]
        
        combined_text = "\n\n---\n\n".join(texts)
        
        prompt = f"""You are summarizing related text chunks to create a higher-level abstraction.
Capture the key themes, concepts, and information while being concise.

Text chunks to summarize:
{combined_text}

Provide a comprehensive summary that captures the essential information from all chunks:"""
        
        try:
            raw = await generate(
                prompt=prompt,
                model=self.model,
                system="You are an expert at creating concise, informative summaries.",
            )
            summary = raw.get("output", "").strip()
            
            if not summary:
                # Fallback: concatenate with ellipsis
                summary = combined_text[:1000] + "..."
            
            logger.info(f"Summarized {len(texts)} chunks into {len(summary)} chars")
            return summary
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return combined_text[:1000] + "..."
    
    async def build_tree(self, document_name: str, raw_text: str) -> dict:
        """
        Build hierarchical RAPTOR tree from document text.
        Returns statistics about the tree structure.
        """
        logger.info(f"=== RAPTOR TREE BUILDING START: {document_name} ===")
        
        # Level 0: Create leaf nodes (base chunks)
        chunks = self._chunk_text(raw_text)
        logger.info(f"Created {len(chunks)} base chunks at Level 0")
        
        if not chunks:
            logger.warning("No chunks created, aborting tree building")
            return {"levels": 0, "total_nodes": 0}
        
        # Embed all base chunks
        embeddings = await self._embed_texts(chunks)
        
        # Create level 0 nodes
        level_nodes = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            node_id = self._generate_node_id(chunk, level=0, index=i)
            node = RAPTORNode(
                node_id=node_id,
                text=chunk,
                embedding=embedding,
                level=0,
                metadata={"document": document_name, "chunk_index": i},
            )
            self.nodes[node_id] = node
            level_nodes.append(node)
        
        logger.info(f"Level 0: {len(level_nodes)} leaf nodes created")
        
        # Build higher levels recursively
        current_level = 0
        all_level_stats = [{"level": 0, "nodes": len(level_nodes)}]
        
        while current_level < self.max_levels - 1 and len(level_nodes) > 1:
            current_level += 1
            logger.info(f"Building Level {current_level}...")
            
            # Extract embeddings and texts from current level
            level_embeddings = [node.embedding for node in level_nodes]
            
            # Cluster similar nodes
            labels, n_clusters = self._cluster_embeddings(level_embeddings)
            
            logger.info(f"Level {current_level}: Formed {n_clusters} clusters")
            
            # Create summary nodes for each cluster
            next_level_nodes = []
            for cluster_id in range(n_clusters):
                # Get all nodes in this cluster
                cluster_indices = np.where(labels == cluster_id)[0]
                cluster_nodes = [level_nodes[i] for i in cluster_indices]
                cluster_texts = [node.text for node in cluster_nodes]
                
                # Summarize cluster
                summary_text = await self._summarize_cluster(cluster_texts)
                
                # Embed summary
                summary_embedding = await get_embedding(summary_text)
                
                # Create parent node
                parent_id = self._generate_node_id(
                    summary_text, level=current_level, index=cluster_id
                )
                parent_node = RAPTORNode(
                    node_id=parent_id,
                    text=summary_text,
                    embedding=summary_embedding,
                    level=current_level,
                    children=[node.node_id for node in cluster_nodes],
                    metadata={
                        "document": document_name,
                        "cluster_id": cluster_id,
                        "children_count": len(cluster_nodes),
                    },
                )
                
                # Update children to point to parent
                for child_node in cluster_nodes:
                    child_node.parent_id = parent_id
                
                self.nodes[parent_id] = parent_node
                next_level_nodes.append(parent_node)
            
            logger.info(f"Level {current_level}: Created {len(next_level_nodes)} summary nodes")
            all_level_stats.append({"level": current_level, "nodes": len(next_level_nodes)})
            
            # Move to next level
            level_nodes = next_level_nodes
            
            # Stop if we've converged to very few nodes
            if len(level_nodes) <= 2:
                logger.info(f"Converged to {len(level_nodes)} nodes, stopping")
                break
        
        total_nodes = len(self.nodes)
        logger.info(f"=== RAPTOR TREE COMPLETE: {total_nodes} total nodes across {current_level + 1} levels ===")
        
        return {
            "document": document_name,
            "levels": current_level + 1,
            "total_nodes": total_nodes,
            "level_breakdown": all_level_stats,
        }
    
    async def retrieve(
        self, query: str, top_k: int = 5, levels_to_search: Optional[list[int]] = None
    ) -> list[tuple[RAPTORNode, float]]:
        """
        Retrieve most relevant nodes from the tree for a query.
        Searches across specified levels (default: all levels).
        Returns list of (node, similarity_score) tuples.
        """
        if not self.nodes:
            logger.warning("RAPTOR tree is empty, no nodes to retrieve")
            return []
        
        # Embed query
        query_embedding = await get_embedding(query)
        query_vector = np.array(query_embedding)
        
        # Determine which levels to search
        if levels_to_search is None:
            # Search all levels
            all_levels = set(node.level for node in self.nodes.values())
            levels_to_search = sorted(all_levels)
        
        logger.info(f"Searching RAPTOR tree across levels: {levels_to_search}")
        
        # Calculate similarities for nodes at specified levels
        candidates = []
        for node in self.nodes.values():
            if node.level in levels_to_search:
                node_vector = np.array(node.embedding)
                # Cosine similarity
                similarity = np.dot(query_vector, node_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(node_vector) + 1e-10
                )
                candidates.append((node, float(similarity)))
        
        # Sort by similarity (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        top_results = candidates[:top_k]
        logger.info(
            f"Retrieved {len(top_results)} nodes with similarities: "
            f"{[f'{score:.3f}' for _, score in top_results[:3]]}"
        )
        
        return top_results


# Global RAPTOR tree instances (keyed by document name)
_raptor_trees: dict[str, RAPTORTree] = {}


async def build_raptor_tree(document_name: str, raw_text: str, **kwargs) -> dict:
    """Build and cache RAPTOR tree for a document."""
    tree = RAPTORTree(**kwargs)
    stats = await tree.build_tree(document_name, raw_text)
    
    # Cache the tree
    _raptor_trees[document_name] = tree
    
    return stats


async def retrieve_from_raptor(
    document_name: str, query: str, top_k: int = 5, **kwargs
) -> list[dict]:
    """
    Retrieve relevant context from RAPTOR tree for a query.
    Returns list of context dictionaries with text and metadata.
    """
    tree = _raptor_trees.get(document_name)
    
    if tree is None:
        logger.warning(f"No RAPTOR tree found for document: {document_name}")
        return []
    
    results = await tree.retrieve(query, top_k=top_k, **kwargs)
    
    # Format results
    contexts = []
    for node, similarity in results:
        contexts.append({
            "text": node.text,
            "level": node.level,
            "similarity": similarity,
            "metadata": node.metadata,
        })
    
    return contexts


def get_raptor_tree_stats(document_name: str) -> Optional[dict]:
    """Get statistics about a cached RAPTOR tree."""
    tree = _raptor_trees.get(document_name)
    if tree is None:
        return None
    
    level_counts = {}
    for node in tree.nodes.values():
        level_counts[node.level] = level_counts.get(node.level, 0) + 1
    
    return {
        "document": document_name,
        "total_nodes": len(tree.nodes),
        "levels": len(level_counts),
        "level_breakdown": [{"level": k, "nodes": v} for k, v in sorted(level_counts.items())],
    }
