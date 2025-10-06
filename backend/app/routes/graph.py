"""
Graph database routes (Neo4j) for health checks, reindexing, and summaries.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Union
import threading
import uuid
from datetime import datetime

from ..auth import get_current_user
from ..database import get_db, Admin, User
from ..config import (
    USE_GRAPH_DB,
    MAX_ENTITIES_PER_CHUNK,
    ENABLE_ENTITY_COOCCURRENCE,
    MAX_COOCCURRENCE_PER_CHUNK,
)
from ..document_store import document_store
from ..graph_db import graph_client
from ..documents import upload_document  # not used directly; keep for consistency

router = APIRouter(prefix="/graph", tags=["Graph"])

# Simple in-memory job store for background reindex
_REINDEX_JOBS = {}
_JOBS_LOCK = threading.Lock()


@router.get("/health")
async def graph_health():
    if not USE_GRAPH_DB:
        return {"enabled": False, "status": "disabled"}
    try:
        return graph_client.health()
    except Exception as e:
        return {"enabled": True, "status": "error", "error": str(e)}


@router.post("/reindex")
async def graph_reindex(
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recreate graph nodes/relations for all docs in the current user's organization.

    - Upserts Document and Chunk nodes
    - Extracts lightweight entities per chunk and links them
    - Creates simple CO_OCCURS_WITH between entities within same chunk
    """
    if not USE_GRAPH_DB:
        raise HTTPException(status_code=400, detail="Graph DB is disabled by configuration")

    try:
        org_id = current_user.OrganizationID
        docs = document_store.get_documents_by_organization(org_id)
        if not docs:
            return {"message": "No documents to index", "indexed": 0}

        from ..docling_chunker import chunk_text_with_docling
        from ..entity_extraction import extract_entities

        indexed = 0
        for doc in docs:
            doc_id = doc.get("id")
            filename = doc.get("filename")
            text = doc.get("extracted_text") or ""
            if not doc_id or not text:
                continue

            # Clear existing doc + chunks
            try:
                graph_client.delete_document(doc_id)
            except Exception:
                pass

            # Upsert document
            graph_client.upsert_document(doc_id, filename or doc_id)

            # Chunk with docling where possible
            try:
                chunks, _ = chunk_text_with_docling(pdf_path=doc.get("file_path", ""), text=text, max_chunk_size=1000)
            except Exception:
                # Very simple sentence split fallback
                sentences = [s.strip() for s in text.split('.') if s.strip()]
                chunks = []
                cur = ''
                for s in sentences:
                    if len(cur) + len(s) > 1000 and cur:
                        chunks.append(cur)
                        cur = s
                    else:
                        cur += (s + '. ')
                if cur:
                    chunks.append(cur)

            # Upsert chunks and relations (bulk)
            chunk_rows = []
            chunk_ids = []
            mentions_rows = []
            entity_rows = []
            cooccur_rows = []
            seen_entities_doc = set()
            for idx, chunk_text in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{idx}"
                chunk_rows.append({"id": chunk_id, "text": chunk_text, "index": idx})
                chunk_ids.append(chunk_id)

                # Entities and relations (capped per chunk)
                ents = []
                local_seen = set()
                for et, ename in extract_entities(chunk_text)[:MAX_ENTITIES_PER_CHUNK]:
                    eid = f"{et}:{ename}"
                    if eid in local_seen:
                        continue
                    local_seen.add(eid)
                    ents.append(eid)
                    if eid not in seen_entities_doc:
                        seen_entities_doc.add(eid)
                        entity_rows.append({"id": eid, "type": et, "name": ename})
                    mentions_rows.append({"chunk_id": chunk_id, "entity_id": eid})
                if ENABLE_ENTITY_COOCCURRENCE and len(ents) > 1:
                    pairs_added = 0
                    for i in range(len(ents)):
                        for j in range(i + 1, len(ents)):
                            if pairs_added >= MAX_COOCCURRENCE_PER_CHUNK:
                                break
                            cooccur_rows.append({"sid": ents[i], "tid": ents[j], "relation": "CO_OCCURS_WITH"})
                            pairs_added += 1

            # Bulk write
            try:
                graph_client.bulk_upsert_chunks(doc_id, chunk_rows)
            except AttributeError:
                # Fallback to per-item if bulk not available (NoOp)
                for row in chunk_rows:
                    graph_client.upsert_chunk(doc_id, row["id"], row["text"], row["index"])
            try:
                graph_client.bulk_relate_document_chunks(doc_id, chunk_ids)
            except AttributeError:
                for cid in chunk_ids:
                    graph_client.relate_document_chunk(doc_id, cid)
            if entity_rows:
                try:
                    graph_client.bulk_upsert_entities(entity_rows)
                except AttributeError:
                    for row in entity_rows:
                        graph_client.upsert_entity(row["type"], row["name"])
            if mentions_rows:
                try:
                    graph_client.bulk_relate_chunk_entities(mentions_rows)
                except AttributeError:
                    for row in mentions_rows:
                        graph_client.relate_chunk_entity(row["chunk_id"], row["entity_id"])
            if cooccur_rows:
                try:
                    graph_client.bulk_relate_entities(cooccur_rows)
                except AttributeError:
                    for row in cooccur_rows:
                        graph_client.relate_entity_entity(row["sid"], row["relation"], row["tid"])

            indexed += 1

        return {"message": "Graph reindex completed", "indexed": indexed, "organization_id": org_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph reindex failed: {str(e)}")


def _run_reindex_for_org(org_id: int):
    """Background worker: reindex graph for all docs in org_id and update job status."""
    job_id = threading.current_thread().name
    with _JOBS_LOCK:
        _REINDEX_JOBS[job_id]["state"] = "running"
        _REINDEX_JOBS[job_id]["started_at"] = datetime.utcnow().isoformat()
    try:
        docs = document_store.get_documents_by_organization(org_id)
        if not docs:
            with _JOBS_LOCK:
                _REINDEX_JOBS[job_id].update({
                    "state": "done",
                    "message": "No documents to index",
                    "indexed": 0,
                    "finished_at": datetime.utcnow().isoformat(),
                })
            return

        from ..docling_chunker import chunk_text_with_docling
        from ..entity_extraction import extract_entities

        indexed = 0
        for doc in docs:
            doc_id = doc.get("id")
            filename = doc.get("filename")
            text = doc.get("extracted_text") or ""
            if not doc_id or not text:
                continue

            try:
                graph_client.delete_document(doc_id)
            except Exception:
                pass

            graph_client.upsert_document(doc_id, filename or doc_id)

            try:
                chunks, _ = chunk_text_with_docling(pdf_path=doc.get("file_path", ""), text=text, max_chunk_size=1000)
            except Exception:
                sentences = [s.strip() for s in text.split('.') if s.strip()]
                chunks = []
                cur = ''
                for s in sentences:
                    if len(cur) + len(s) > 1000 and cur:
                        chunks.append(cur)
                        cur = s
                    else:
                        cur += (s + '. ')
                if cur:
                    chunks.append(cur)

            chunk_rows = []
            chunk_ids = []
            mentions_rows = []
            entity_rows = []
            cooccur_rows = []
            seen_entities_doc = set()
            for idx, chunk_text in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{idx}"
                chunk_rows.append({"id": chunk_id, "text": chunk_text, "index": idx})
                chunk_ids.append(chunk_id)

                ents = []
                local_seen = set()
                for et, ename in extract_entities(chunk_text)[:MAX_ENTITIES_PER_CHUNK]:
                    eid = f"{et}:{ename}"
                    if eid in local_seen:
                        continue
                    local_seen.add(eid)
                    ents.append(eid)
                    if eid not in seen_entities_doc:
                        seen_entities_doc.add(eid)
                        entity_rows.append({"id": eid, "type": et, "name": ename})
                    mentions_rows.append({"chunk_id": chunk_id, "entity_id": eid})
                if ENABLE_ENTITY_COOCCURRENCE and len(ents) > 1:
                    pairs_added = 0
                    for i in range(len(ents)):
                        for j in range(i + 1, len(ents)):
                            if pairs_added >= MAX_COOCCURRENCE_PER_CHUNK:
                                break
                            cooccur_rows.append({"sid": ents[i], "tid": ents[j], "relation": "CO_OCCURS_WITH"})
                            pairs_added += 1

            try:
                graph_client.bulk_upsert_chunks(doc_id, chunk_rows)
            except AttributeError:
                for row in chunk_rows:
                    graph_client.upsert_chunk(doc_id, row["id"], row["text"], row["index"])
            try:
                graph_client.bulk_relate_document_chunks(doc_id, chunk_ids)
            except AttributeError:
                for cid in chunk_ids:
                    graph_client.relate_document_chunk(doc_id, cid)
            if entity_rows:
                try:
                    graph_client.bulk_upsert_entities(entity_rows)
                except AttributeError:
                    for row in entity_rows:
                        graph_client.upsert_entity(row["type"], row["name"])
            if mentions_rows:
                try:
                    graph_client.bulk_relate_chunk_entities(mentions_rows)
                except AttributeError:
                    for row in mentions_rows:
                        graph_client.relate_chunk_entity(row["chunk_id"], row["entity_id"])
            if cooccur_rows:
                try:
                    graph_client.bulk_relate_entities(cooccur_rows)
                except AttributeError:
                    for row in cooccur_rows:
                        graph_client.relate_entity_entity(row["sid"], row["relation"], row["tid"])

            indexed += 1
            with _JOBS_LOCK:
                _REINDEX_JOBS[job_id]["indexed"] = indexed

        with _JOBS_LOCK:
            _REINDEX_JOBS[job_id].update({
                "state": "done",
                "message": "Graph reindex completed",
                "finished_at": datetime.utcnow().isoformat(),
            })
    except Exception as e:
        with _JOBS_LOCK:
            _REINDEX_JOBS[job_id].update({
                "state": "error",
                "error": str(e),
                "finished_at": datetime.utcnow().isoformat(),
            })


@router.post("/reindex/background")
async def graph_reindex_background(
    background_tasks: BackgroundTasks,
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kick off a background reindex job to avoid blocking and noisy output."""
    if not USE_GRAPH_DB:
        raise HTTPException(status_code=400, detail="Graph DB is disabled by configuration")

    org_id = current_user.OrganizationID
    job_id = str(uuid.uuid4())
    with _JOBS_LOCK:
        _REINDEX_JOBS[job_id] = {
            "id": job_id,
            "state": "queued",
            "organization_id": org_id,
            "indexed": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
    # Name the thread with job_id for lookup inside worker
    t = threading.Thread(target=_run_reindex_for_org, name=job_id, args=(org_id,), daemon=True)
    t.start()
    return {"job_id": job_id, "state": "queued"}


@router.get("/reindex/status/{job_id}")
async def graph_reindex_status(job_id: str):
    with _JOBS_LOCK:
        job = _REINDEX_JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job


@router.get("/document/{document_id}/summary")
async def graph_document_summary(
    document_id: str,
    current_user: Union[Admin, User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not USE_GRAPH_DB:
        raise HTTPException(status_code=400, detail="Graph DB is disabled by configuration")
    # Ensure doc belongs to user's organization
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("organization_id") != current_user.OrganizationID:
        raise HTTPException(status_code=403, detail="Access denied: Document belongs to different organization")

    try:
        return graph_client.get_document_summary(document_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph summary: {str(e)}")
