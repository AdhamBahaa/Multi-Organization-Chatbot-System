"""
Neo4j graph client with graceful fallback when disabled or driver missing.
"""
from typing import List, Dict, Optional
from .config import USE_GRAPH_DB, GRAPH_DB_URI, GRAPH_DB_USER, GRAPH_DB_PASSWORD

class NoOpGraphClient:
    def health(self) -> Dict:
        return {"enabled": False, "status": "disabled"}
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
    def delete_document(self, doc_id: str):
        pass
    def get_document_summary(self, doc_id: str) -> Dict:
        return {"document_id": doc_id, "chunks": 0, "entities": 0}
    def expand_related_for_chunks(self, chunk_ids: List[str], max_neighbors: int = 5) -> List[Dict]:
        return []
    # Visualization helpers (no-op)
    def search_entities(self, q: str, limit: int = 10) -> List[Dict]:
        return []
    def get_subgraph_for_entities(self, entities: List[str], max_neighbors: int = 10) -> Dict:
        return {"nodes": [], "edges": []}
    def get_subgraph_for_chunks(self, chunk_ids: List[str], max_neighbors: int = 5) -> Dict:
        return {"nodes": [], "edges": []}
    def get_ego_network(self, center_entities: List[str], depth: int = 1, limit: int = 30) -> Dict:
        return {"nodes": [], "edges": []}

try:
    if USE_GRAPH_DB:
        from neo4j import GraphDatabase  # type: ignore

        class Neo4jGraphClient:
            def __init__(self, uri: str, user: str, password: str):
                # Use a short connection timeout so bad routing/connection fails fast instead of hanging
                # Note: prefer bolt:// for single-instance community servers. neo4j:// may attempt routing and hang.
                self.driver = GraphDatabase.driver(
                    uri,
                    auth=(user, password),
                    connection_timeout=10,
                )

            def close(self):
                self.driver.close()

            def health(self) -> Dict:
                try:
                    with self.driver.session() as session:
                        rec = session.run("RETURN 1 as ok").single()
                        return {"enabled": True, "status": "ok", "ok": rec["ok"] == 1}
                except Exception as e:
                    return {"enabled": True, "status": "error", "error": str(e)}

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

            # Bulk helpers to reduce round-trips
            def bulk_upsert_chunks(self, doc_id: str, items: List[Dict]):
                """items: [{id, text, index}]"""
                cypher = (
                    "UNWIND $rows as row "
                    "MERGE (c:Chunk {id: row.id}) SET c.text = row.text, c.index = row.index"
                )
                with self.driver.session() as session:
                    session.run(cypher, rows=items)

            def bulk_relate_document_chunks(self, doc_id: str, chunk_ids: List[str]):
                cypher = (
                    "MATCH (d:Document {id: $doc_id}) "
                    "UNWIND $ids as cid "
                    "MATCH (c:Chunk {id: cid}) "
                    "MERGE (d)-[:HAS_CHUNK]->(c)"
                )
                with self.driver.session() as session:
                    session.run(cypher, doc_id=doc_id, ids=chunk_ids)

            def bulk_upsert_entities(self, items: List[Dict]):
                """items: [{id, type, name}]"""
                cypher = (
                    "UNWIND $rows as row "
                    "MERGE (e:Entity {id: row.id}) SET e.type = row.type, e.name = row.name"
                )
                with self.driver.session() as session:
                    session.run(cypher, rows=items)

            def bulk_relate_chunk_entities(self, items: List[Dict]):
                """items: [{chunk_id, entity_id}]"""
                cypher = (
                    "UNWIND $rows as row "
                    "MATCH (c:Chunk {id: row.chunk_id}), (e:Entity {id: row.entity_id}) "
                    "MERGE (c)-[:MENTIONS]->(e)"
                )
                with self.driver.session() as session:
                    session.run(cypher, rows=items)

            def bulk_relate_entities(self, items: List[Dict]):
                """items: [{sid, tid, relation}]"""
                cypher = (
                    "UNWIND $rows as row "
                    "MATCH (s:Entity {id: row.sid}), (t:Entity {id: row.tid}) "
                    "MERGE (s)-[:RELATED_TO {relation: row.relation}]->(t)"
                )
                with self.driver.session() as session:
                    session.run(cypher, rows=items)

            def delete_document(self, doc_id: str):
                # Detach delete the document and its chunks; keep entities (they may be shared)
                cypher = (
                    "MATCH (d:Document {id: $doc_id})-[:HAS_CHUNK]->(c:Chunk) "
                    "DETACH DELETE c "
                )
                cypher_doc = "MATCH (d:Document {id: $doc_id}) DETACH DELETE d"
                with self.driver.session() as session:
                    session.run(cypher, doc_id=doc_id)
                    session.run(cypher_doc, doc_id=doc_id)

            def get_document_summary(self, doc_id: str) -> Dict:
                cypher = (
                    "MATCH (d:Document {id: $doc_id})-[:HAS_CHUNK]->(c:Chunk) "
                    "OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity) "
                    "RETURN count(distinct c) as chunks, count(distinct e) as entities"
                )
                with self.driver.session() as session:
                    rec = session.run(cypher, doc_id=doc_id).single()
                    if rec:
                        return {"document_id": doc_id, "chunks": rec["chunks"], "entities": rec["entities"]}
                    return {"document_id": doc_id, "chunks": 0, "entities": 0}

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

            def ensure_schema(self):
                """Create helpful constraints if they don't already exist."""
                stmts = [
                    "CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
                    "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                ]
                with self.driver.session() as session:
                    for s in stmts:
                        try:
                            session.run(s)
                        except Exception:
                            pass

            # ---------- Visualization helpers ----------
            def _prop(self, obj, key: str, default=None):
                """Safely read a property from Neo4j Node/Relationship or dict."""
                if obj is None:
                    return default
                # Dict-like
                if isinstance(obj, dict):
                    return obj.get(key, default)
                # Neo4j types implement __getitem__ for properties
                try:
                    return obj[key]
                except Exception:
                    # As a last resort, try attribute access
                    return getattr(obj, key, default)

            def _to_vis(self, records: List[Dict]) -> Dict:
                nodes = {}
                edges = set()
                for rec in records:
                    # Entities
                    e = rec.get("e")
                    if e:
                        e_id = self._prop(e, "id")
                        if e_id is not None:
                            nodes[("Entity", e_id)] = {
                                "id": e_id,
                                "label": self._prop(e, "name") or e_id,
                                "type": "Entity",
                            }
                    e2 = rec.get("e2")
                    if e2:
                        e2_id = self._prop(e2, "id")
                        if e2_id is not None:
                            nodes[("Entity", e2_id)] = {
                                "id": e2_id,
                                "label": self._prop(e2, "name") or e2_id,
                                "type": "Entity",
                            }
                    # Chunks
                    c = rec.get("c")
                    if c:
                        c_id = self._prop(c, "id")
                        if c_id is not None:
                            nodes[("Chunk", c_id)] = {
                                "id": c_id,
                                "label": c_id,
                                "type": "Chunk",
                                "text": self._prop(c, "text", ""),
                            }
                    # Documents
                    d = rec.get("d")
                    if d:
                        d_id = self._prop(d, "id")
                        if d_id is not None:
                            nodes[("Document", d_id)] = {
                                "id": d_id,
                                "label": self._prop(d, "filename") or d_id,
                                "type": "Document",
                            }
                    # Edges
                    r = rec.get("r")
                    if r and e and e2:
                        e_id = self._prop(e, "id")
                        e2_id = self._prop(e2, "id")
                        rel = self._prop(r, "relation", "RELATED_TO")
                        if e_id and e2_id:
                            edges.add((e_id, e2_id, rel))
                    if c and e:
                        c_id = self._prop(c, "id")
                        e_id = self._prop(e, "id")
                        if c_id and e_id:
                            edges.add((c_id, e_id, "MENTIONS"))
                    if d and c:
                        d_id = self._prop(d, "id")
                        c_id = self._prop(c, "id")
                        if d_id and c_id:
                            edges.add((d_id, c_id, "HAS_CHUNK"))
                return {
                    "nodes": list(nodes.values()),
                    "edges": [
                        {"source": s, "target": t, "label": lab} for (s, t, lab) in edges
                    ],
                }

            def search_entities(self, q: str, limit: int = 10) -> List[Dict]:
                cypher = (
                    "MATCH (e:Entity) WHERE toLower(e.name) CONTAINS toLower($q) "
                    "RETURN e ORDER BY e.name LIMIT $limit"
                )
                with self.driver.session() as session:
                    result = session.run(cypher, q=q, limit=limit)
                    out: List[Dict] = []
                    for rec in result:
                        e = rec["e"]
                        out.append({
                            "id": self._prop(e, "id"),
                            "name": self._prop(e, "name"),
                            "type": self._prop(e, "type"),
                        })
                    return out

            def get_subgraph_for_entities(self, entities: List[str], max_neighbors: int = 10) -> Dict:
                # entities can be ids (type:name) or names; resolve both
                cypher = (
                    "UNWIND $entities as q "
                    "MATCH (e:Entity) WHERE e.id = q OR e.name = q "
                    "WITH e LIMIT 10 "
                    "OPTIONAL MATCH (e)-[r:RELATED_TO]->(e2:Entity) "
                    "WITH e, r, e2 ORDER BY e2.name LIMIT $k "
                    "RETURN e as e, r as r, e2 as e2"
                )
                with self.driver.session() as session:
                    result = session.run(cypher, entities=entities, k=max_neighbors)
                    return self._to_vis([record.data() for record in result])

            def get_subgraph_for_chunks(self, chunk_ids: List[str], max_neighbors: int = 5) -> Dict:
                cypher = (
                    "UNWIND $cids as cid "
                    "MATCH (c:Chunk {id: cid}) "
                    "WITH c LIMIT 20 "
                    "OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity) "
                    "WITH c, e LIMIT $k "
                    "OPTIONAL MATCH (e)-[r:RELATED_TO]->(e2:Entity) "
                    "WITH c, e, r, e2 LIMIT $k "
                    "OPTIONAL MATCH (d:Document)-[:HAS_CHUNK]->(c) "
                    "RETURN c as c, e as e, r as r, e2 as e2, d as d"
                )
                with self.driver.session() as session:
                    result = session.run(cypher, cids=chunk_ids)
                    return self._to_vis([record.data() for record in result])

            def get_ego_network(self, center_entities: List[str], depth: int = 1, limit: int = 50) -> Dict:
                # bounded BFS on entities graph
                cypher = (
                    "UNWIND $centers as q "
                    "MATCH (e:Entity) WHERE e.id = q OR e.name = q "
                    "CALL apoc.path.expandConfig(e, {relationshipFilter:'RELATED_TO>', maxLevel:$depth, bfs:true, limit:$limit}) YIELD path "
                    "WITH path "
                    "UNWIND relationships(path) as r "
                    "WITH startNode(r) as e, r as r, endNode(r) as e2 "
                    "RETURN e as e, r as r, e2 as e2"
                )
                with self.driver.session() as session:
                    try:
                        result = session.run(cypher, centers=center_entities, depth=depth, limit=limit)
                        return self._to_vis([record.data() for record in result])
                    except Exception:
                        # Fallback without APOC
                        cypher2 = (
                            "UNWIND $centers as q "
                            "MATCH (e:Entity) WHERE e.id = q OR e.name = q "
                            "OPTIONAL MATCH (e)-[r:RELATED_TO]->(e2:Entity) "
                            "RETURN e as e, r as r, e2 as e2"
                        )
                        res2 = session.run(cypher2, centers=center_entities)
                        return self._to_vis([record.data() for record in res2])

        graph_client = Neo4jGraphClient(GRAPH_DB_URI, GRAPH_DB_USER, GRAPH_DB_PASSWORD)
    else:
        graph_client = NoOpGraphClient()
except Exception:
    graph_client = NoOpGraphClient()


