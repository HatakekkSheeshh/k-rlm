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
            logger.info(f"Connecting to Neo4j at {settings.neo4j_uri}...")
            self._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
            )
            await self._driver.verify_connectivity()
            logger.info("Connected to Neo4j.")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
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
            logger.warning("No nodes to insert.")
            return

        async with self._driver.session() as session:
            try:
                await session.run(
                    "MATCH (n {source_document: $doc}) DETACH DELETE n", doc=document_name
                )

                for node in graph_result.nodes:
                    label = safe_label(node.label)
                    props = node.properties or {}
                    props["source_document"] = document_name
                    props["name"] = node.id

                    query = f"MERGE (n:`{label}` {{id: $id}}) SET n += $props"
                    await session.run(query, id=node.id, props=props)

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

                logger.info(f"Inserted {len(graph_result.nodes)} nodes, {len(graph_result.edges)} edges")
            except Exception as e:
                logger.error(f"Error inserting into Neo4j: {e}")

    async def detect_communities(self, document_name: str) -> list[Community]:
        """Detect communities via label grouping + connected components."""
        if not self._driver:
            logger.warning("Neo4j driver not initialized, skipping community detection.")
            return []

        async with self._driver.session() as session:
            try:
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

                    edges = await self._get_community_edges_by_label(document_name, record["label"])

                    communities.append(
                        Community(community_id=community_id, nodes=nodes, edges=edges)
                    )
                    community_id += 1

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
        """Detect communities as connected components."""
        if not self._driver:
            return []

        communities = []
        community_id = 100

        async with self._driver.session() as session:
            try:
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
                    nodes_result = await session.run(
                        "MATCH (n {source_document: $doc}) RETURN n.id AS id, labels(n)[0] AS label, properties(n) AS properties",
                        doc=document_name,
                    )
                    edges_result = await session.run(
                        "MATCH (a {source_document: $doc})-[r]->(b {source_document: $doc}) RETURN a.id AS source, b.id AS target, type(r) AS relation",
                        doc=document_name,
                    )
                else:
                    nodes_result = await session.run("MATCH (n) RETURN n.id AS id, labels(n)[0] AS label, properties(n) AS properties")
                    edges_result = await session.run("MATCH (a)-[r]->(b) RETURN a.id AS source, b.id AS target, type(r) AS relation")

                nodes = [{"id": r["id"], "label": r["label"], "properties": r["properties"]} async for r in nodes_result]
                edges = [{"source": r["source"], "target": r["target"], "relation": r["relation"]} async for r in edges_result]

                return {"nodes": nodes, "edges": edges}

            except Exception as e:
                logger.error(f"Error getting full graph: {e}")
                return {"nodes": [], "edges": []}

    async def search_entities(self, query: str, limit: int = 10) -> dict:
        """Search for entities matching query keywords."""
        if not self._driver:
            logger.warning("Neo4j driver not initialized, skipping search.")
            return {"nodes": [], "edges": []}

        keywords = [w.strip().lower() for w in query.split() if len(w.strip()) > 2]

        async with self._driver.session() as session:
            try:
                if keywords:
                    conditions = " OR ".join([
                        f"toLower(n.id) CONTAINS '{kw}' OR toLower(labels(n)[0]) CONTAINS '{kw}'"
                        for kw in keywords
                    ])
                    cypher = f"MATCH (n) WHERE {conditions} RETURN n.id AS id, labels(n)[0] AS label, properties(n) AS properties LIMIT {limit}"
                else:
                    cypher = f"MATCH (n) RETURN n.id AS id, labels(n)[0] AS label, properties(n) AS properties LIMIT {limit}"

                nodes = [{"id": r["id"], "label": r["label"], "properties": r["properties"]} async for r in await session.run(cypher)]

                if nodes:
                    node_ids = [n["id"] for n in nodes]
                    edges = [{"source": r["source"], "target": r["target"], "relation": r["relation"]} async for r in await session.run(
                        "MATCH (a)-[r]->(b) WHERE a.id IN $node_ids OR b.id IN $node_ids RETURN a.id AS source, b.id AS target, type(r) AS relation LIMIT 20",
                        node_ids=node_ids
                    )]
                    return {"nodes": nodes, "edges": edges}

                return {"nodes": nodes, "edges": []}

            except Exception as e:
                logger.error(f"Error searching entities: {e}")
                return {"nodes": [], "edges": []}


neo4j_client = Neo4jClient()
