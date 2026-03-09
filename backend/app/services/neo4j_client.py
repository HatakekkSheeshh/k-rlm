import logging
import re
from typing import Optional
from neo4j import AsyncGraphDatabase

from app.config import settings

logger = logging.getLogger(__name__)


def safe_label(name: str) -> str:
    """Sanitize a string to be safely used as a Neo4j label or relationship type."""
    if not name:
        return "UNKNOWN"
    clean = re.sub(r"[\s\-]+", "_", name)
    clean = re.sub(r"[^a-zA-Z0-9_]", "", clean)
    return clean.upper() if clean else "UNKNOWN"


class Community:
    """Represents a detected community in the graph."""

    def __init__(self, community_id: int, nodes: list[dict], edges: list[dict]):
        self.id = community_id
        self.nodes = nodes
        self.edges = edges

    def context_text(self) -> str:
        """Build a text representation of this community for summarization."""
        lines = []
        for n in self.nodes:
            lines.append(f"Entity: {n['id']} (type: {n.get('label', 'UNKNOWN')})")
        for e in self.edges:
            lines.append(f"Relation: {e['source']} --[{e['relation']}]--> {e['target']}")
        return "\n".join(lines)


class Neo4jClient:
    def __init__(self):
        self._driver = None

    async def connect(self):
        try:
            self._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
            )
            await self._driver.verify_connectivity()
            logger.info("Connected to Neo4j successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._driver = None

    async def close(self):
        if self._driver:
            await self._driver.close()
            logger.info("Neo4j connection closed.")

    async def insert_graph_result(self, document_name: str, graph_result):
        """Insert nodes and edges into Neo4j."""
        if not self._driver:
            logger.warning("Neo4j driver not initialized, skipping insert.")
            return

        if not graph_result or not graph_result.nodes:
            logger.warning("No nodes to insert into Neo4j.")
            return

        async with self._driver.session() as session:
            try:
                # First, clear any existing data for this document
                await session.run(
                    "MATCH (n {source_document: $doc}) DETACH DELETE n", doc=document_name
                )

                # Insert Nodes
                for node in graph_result.nodes:
                    label = safe_label(node.label)
                    props = node.properties or {}
                    props["source_document"] = document_name
                    props["name"] = node.id  # Force Neo4j Browser to display node.id as caption

                    query = f"""
                    MERGE (n:`{label}` {{id: $id}})
                    SET n += $props
                    """
                    await session.run(query, id=node.id, props=props)

                # Insert Edges
                for edge in graph_result.edges:
                    rel_type = safe_label(edge.relation)
                    props = edge.properties or {}
                    props["source_document"] = document_name

                    query = f"""
                    MATCH (source {{id: $source_id}})
                    MATCH (target {{id: $target_id}})
                    MERGE (source)-[r:`{rel_type}`]->(target)
                    SET r += $props
                    """
                    await session.run(
                        query, source_id=edge.source, target_id=edge.target, props=props
                    )

                logger.info(
                    f"Inserted {len(graph_result.nodes)} nodes, {len(graph_result.edges)} edges"
                )
            except Exception as e:
                logger.error(f"Error inserting into Neo4j: {e}")

    async def detect_communities(self, document_name: str) -> list[Community]:
        """
        Detect communities using label-based grouping.
        Each node label (PERSON, ORG, etc.) becomes a community.
        """
        if not self._driver:
            logger.warning("Neo4j driver not initialized, skipping community detection.")
            return []

        async with self._driver.session() as session:
            try:
                # Get nodes grouped by their label (type)
                result = await session.run(
                    """
                    MATCH (n {source_document: $doc})
                    RETURN labels(n)[0] AS label,
                           collect(DISTINCT {
                               id: n.id,
                               label: labels(n)[0],
                               properties: properties(n)
                           }) AS nodes
                    ORDER BY size(nodes) DESC
                """,
                    doc=document_name,
                )

                communities = []
                community_id = 0

                async for record in result:
                    nodes = record["nodes"]
                    if not nodes:
                        continue

                    # Get edges within this community (by label)
                    edges = await self._get_community_edges_by_label(document_name, record["label"])

                    communities.append(
                        Community(community_id=community_id, nodes=nodes, edges=edges)
                    )
                    community_id += 1

                # Also detect cross-label communities (connected components)
                cross_communities = await self._detect_connected_components(document_name)
                communities.extend(cross_communities)

                logger.info(f"Detected {len(communities)} communities")
                return communities

            except Exception as e:
                logger.error(f"Error detecting communities: {e}")
                return []

    async def _get_community_edges_by_label(self, document_name: str, label: str) -> list[dict]:
        """Get edges within nodes of a specific label."""
        if not self._driver:
            return []

        async with self._driver.session() as session:
            try:
                result = await session.run(
                    """
                    MATCH (a:`{label}` {source_document: $doc})-[r]->(b:`{label}` {source_document: $doc})
                    RETURN a.id AS source, b.id AS target, type(r) AS relation
                """.format(label=label),
                    doc=document_name,
                )

                edges = []
                async for record in result:
                    edges.append(
                        {
                            "source": record["source"],
                            "target": record["target"],
                            "relation": record["relation"],
                        }
                    )
                return edges
            except Exception as e:
                logger.error(f"Error getting edges by label: {e}")
                return []

    async def _detect_connected_components(self, document_name: str) -> list[Community]:
        """
        Detect communities as connected components (nodes that are interconnected).
        This finds groups of nodes that are linked to each other.
        """
        if not self._driver:
            return []

        communities = []
        community_id = 100  # Start after label-based communities

        async with self._driver.session() as session:
            try:
                # Find nodes with relationships
                result = await session.run(
                    """
                    MATCH (n {source_document: $doc})-[r]->(m {source_document: $doc})
                    WITH collect(DISTINCT n.id) AS connectedNodes
                    WHERE size(connectedNodes) > 1
                    RETURN connectedNodes
                """,
                    doc=document_name,
                )

                async for record in result:
                    node_ids = record["connectedNodes"]
                    if len(node_ids) < 2:
                        continue

                    # Get full node info
                    nodes_result = await session.run(
                        """
                        MATCH (n {source_document: $doc})
                        WHERE n.id IN $nodeIds
                        RETURN n.id AS id, labels(n)[0] AS label, properties(n) AS properties
                    """,
                        doc=document_name,
                        nodeIds=node_ids,
                    )

                    nodes = []
                    async for n_record in nodes_result:
                        nodes.append(
                            {
                                "id": n_record["id"],
                                "label": n_record["label"],
                                "properties": n_record["properties"],
                            }
                        )

                    # Get edges among these nodes
                    edges_result = await session.run(
                        """
                        MATCH (a {source_document: $doc})-[r]->(b {source_document: $doc})
                        WHERE a.id IN $nodeIds AND b.id IN $nodeIds
                        RETURN a.id AS source, b.id AS target, type(r) AS relation
                    """,
                        doc=document_name,
                        nodeIds=node_ids,
                    )

                    edges = []
                    async for e_record in edges_result:
                        edges.append(
                            {
                                "source": e_record["source"],
                                "target": e_record["target"],
                                "relation": e_record["relation"],
                            }
                        )

                    if nodes:
                        communities.append(
                            Community(community_id=community_id, nodes=nodes, edges=edges)
                        )
                        community_id += 1

                return communities

            except Exception as e:
                logger.error(f"Error detecting connected components: {e}")
                return []

    async def get_full_graph(self, document_name: Optional[str] = None) -> dict:
        """Retrieve the full graph for visualization."""
        if not self._driver:
            return {"nodes": [], "edges": []}

        async with self._driver.session() as session:
            try:
                if document_name:
                    # Get nodes for specific document
                    nodes_result = await session.run(
                        """
                        MATCH (n {source_document: $doc})
                        RETURN n.id AS id, labels(n)[0] AS label, properties(n) AS properties
                    """,
                        doc=document_name,
                    )

                    nodes = []
                    async for record in nodes_result:
                        nodes.append(
                            {
                                "id": record["id"],
                                "label": record["label"],
                                "properties": record["properties"],
                            }
                        )

                    # Get edges
                    edges_result = await session.run(
                        """
                        MATCH (a {source_document: $doc})-[r]->(b {source_document: $doc})
                        RETURN a.id AS source, b.id AS target, type(r) AS relation
                    """,
                        doc=document_name,
                    )

                    edges = []
                    async for record in edges_result:
                        edges.append(
                            {
                                "source": record["source"],
                                "target": record["target"],
                                "relation": record["relation"],
                            }
                        )
                else:
                    # Get all nodes
                    nodes_result = await session.run("""
                        MATCH (n)
                        RETURN n.id AS id, labels(n)[0] AS label, properties(n) AS properties
                    """)
                    nodes = []
                    async for record in nodes_result:
                        nodes.append(
                            {
                                "id": record["id"],
                                "label": record["label"],
                                "properties": record["properties"],
                            }
                        )

                    # Get all edges
                    edges_result = await session.run("""
                        MATCH (a)-[r]->(b)
                        RETURN a.id AS source, b.id AS target, type(r) AS relation
                    """)
                    edges = []
                    async for record in edges_result:
                        edges.append(
                            {
                                "source": record["source"],
                                "target": record["target"],
                                "relation": record["relation"],
                            }
                        )

                return {"nodes": nodes, "edges": edges}

            except Exception as e:
                logger.error(f"Error getting full graph: {e}")
                return {"nodes": [], "edges": []}


neo4j_client = Neo4jClient()
