"""
Neo4j graph client with graceful fallback when disabled or driver missing.
"""
from typing import List, Dict, Optional
from .config import USE_GRAPH_DB, GRAPH_DB_URI, GRAPH_DB_USER, GRAPH_DB_PASSWORD

class NoOpGraphClient:
    def upsert_document(self, doc_id: str, filename: str):
        pass
    def upsert_chunk(self, doc_id: str, chunk_id: str, text: str, index: int):
        pass
    def relate_document_chunk(self, doc_id: str, chunk_id: str):
        pass
    def upsert_entity(self, entity_type: str, name: str) -> str:
        return ""
    def relate_chunk_entity(self, chunk_id: str, entity_id: str):
        pass
    def relate_entity_entity(self, source_id: str, relation: str, target_id: str):
        pass
    def expand_related_for_chunks(self, chunk_ids: List[str], max_neighbors: int = 5) -> List[Dict]:
        return []

try:
    if USE_GRAPH_DB:
        from neo4j import GraphDatabase  # type: ignore

        class Neo4jGraphClient:
            def __init__(self, uri: str, user: str, password: str):
                self.driver = GraphDatabase.driver(uri, auth=(user, password))

            def close(self):
                self.driver.close()

            def upsert_document(self, doc_id: str, filename: str):
                cypher = (
                    "MERGE (d:Document {id: $id}) SET d.filename = $filename"
                )
                with self.driver.session() as session:
                    session.run(cypher, id=doc_id, filename=filename)

            def upsert_chunk(self, doc_id: str, chunk_id: str, text: str, index: int):
                cypher = (
                    "MERGE (c:Chunk {id: $id}) SET c.text = $text, c.index = $index"
                )
                with self.driver.session() as session:
                    session.run(cypher, id=chunk_id, text=text, index=index)

            def relate_document_chunk(self, doc_id: str, chunk_id: str):
                cypher = (
                    "MATCH (d:Document {id: $doc_id}), (c:Chunk {id: $chunk_id}) "
                    "MERGE (d)-[:HAS_CHUNK]->(c)"
                )
                with self.driver.session() as session:
                    session.run(cypher, doc_id=doc_id, chunk_id=chunk_id)

            def upsert_entity(self, entity_type: str, name: str) -> str:
                entity_id = f"{entity_type}:{name}"
                cypher = (
                    "MERGE (e:Entity {id: $id}) SET e.type = $type, e.name = $name"
                )
                with self.driver.session() as session:
                    session.run(cypher, id=entity_id, type=entity_type, name=name)
                return entity_id

            def relate_chunk_entity(self, chunk_id: str, entity_id: str):
                cypher = (
                    "MATCH (c:Chunk {id: $chunk_id}), (e:Entity {id: $entity_id}) "
                    "MERGE (c)-[:MENTIONS]->(e)"
                )
                with self.driver.session() as session:
                    session.run(cypher, chunk_id=chunk_id, entity_id=entity_id)

            def relate_entity_entity(self, source_id: str, relation: str, target_id: str):
                cypher = (
                    "MATCH (s:Entity {id: $sid}), (t:Entity {id: $tid}) "
                    f"MERGE (s)-[:RELATED_TO {{relation: $relation}}]->(t)"
                )
                with self.driver.session() as session:
                    session.run(cypher, sid=source_id, tid=target_id, relation=relation)

            def expand_related_for_chunks(self, chunk_ids: List[str], max_neighbors: int = 5) -> List[Dict]:
                cypher = (
                    "MATCH (c:Chunk)-[:MENTIONS]->(e:Entity) "
                    "WHERE c.id IN $chunk_ids "
                    "OPTIONAL MATCH (e)-[r:RELATED_TO]->(e2:Entity) "
                    "RETURN c.id as chunk_id, collect(distinct e.name)[0..$k] as entities, "
                    "collect(distinct {name: e2.name, relation: r.relation})[0..$k] as neighbors"
                )
                with self.driver.session() as session:
                    result = session.run(cypher, chunk_ids=chunk_ids, k=max_neighbors)
                    return [record.data() for record in result]

        graph_client = Neo4jGraphClient(GRAPH_DB_URI, GRAPH_DB_USER, GRAPH_DB_PASSWORD)
    else:
        graph_client = NoOpGraphClient()
except Exception:
    graph_client = NoOpGraphClient()


