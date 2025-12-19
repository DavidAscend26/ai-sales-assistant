from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import KnowledgeChunk
from app.rag.embeddings import Embedder
from app.rag.qdrant_store import get_client

logger = logging.getLogger(__name__)
_embedder = Embedder()

async def retrieve_kavak_knowledge(session: AsyncSession, query: str, top_k: int = 4) -> list[dict]:
    # 1) Intento vectorial con Qdrant (API async compatible)
    try:
        client = await get_client()
        qvec = _embedder.embed([query])[0]

        # API nueva: query_points()
        if hasattr(client, "query_points"):
            resp = await client.query_points(
                collection_name=settings.QDRANT_COLLECTION,
                query=qvec,
                limit=top_k,
                with_payload=True,
            )
            hits = getattr(resp, "points", None) or []
            results = []
            for p in hits:
                payload = p.payload or {}
                content = payload.get("content")
                if not content:
                    continue
                results.append(
                    {
                        "source": payload.get("source"),
                        "title": payload.get("title"),
                        "content": content,
                        "score": float(getattr(p, "score", 0.0) or 0.0),
                    }
                )
            if results:
                return results[:top_k]

        # API vieja (sync o async dependiendo versión): search()
        if hasattr(client, "search"):
            hits = await client.search(  # type: ignore[attr-defined]
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=qvec,
                limit=top_k,
                with_payload=True,
            )
            results = []
            for h in hits:
                payload = getattr(h, "payload", None) or {}
                content = payload.get("content")
                if not content:
                    continue
                results.append(
                    {
                        "source": payload.get("source"),
                        "title": payload.get("title"),
                        "content": content,
                        "score": float(getattr(h, "score", 0.0) or 0.0),
                    }
                )
            if results:
                return results[:top_k]

        logger.warning("El cliente Qdrant no tiene query_points() ni search(). Se recurre a Postgres.")
    except Exception:
        logger.exception("Error en la recuperación de Qdrant. Se está volviendo a Postgres.")

    # 2) Fallback: Postgres. Nunca falla si hay chunks.
    stmt = select(KnowledgeChunk).order_by(KnowledgeChunk.id.desc()).limit(top_k)
    rows = (await session.execute(stmt)).scalars().all()
    return [{"source": r.source, "title": r.title, "content": r.content, "score": 0.0} for r in rows]