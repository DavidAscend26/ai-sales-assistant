import argparse
import asyncio
import hashlib
from typing import List

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import delete

from qdrant_client.models import PointStruct

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import KnowledgeChunk
from app.rag.embeddings import Embedder
from app.rag.qdrant_store import get_client, ensure_collection, upsert_points


KAVAK_URL = "https://www.kavak.com/mx/blog/sedes-de-kavak-en-mexico"


def chunk_text(text: str, max_chars: int = 900) -> List[str]:
    """
    Divide texto largo en chunks semánticos simples (por párrafos),
    garantizando un tamaño máximo.
    """
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: List[str] = []

    buff = ""
    for p in paragraphs:
        if len(buff) + len(p) <= max_chars:
            buff = f"{buff}\n{p}".strip()
        else:
            if buff:
                chunks.append(buff)
            buff = p

    if buff:
        chunks.append(buff)

    return chunks


def stable_point_id(source: str, content: str) -> int:
    """
    Genera un ID estable para Qdrant basado en hash.
    Evita duplicados al re-ingestar.
    """
    h = hashlib.sha256(f"{source}:{content}".encode("utf-8")).hexdigest()
    return int(h[:16], 16)


async def fetch_kavak_page() -> tuple[str, str]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(KAVAK_URL)
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    title = soup.title.text.strip() if soup.title else "Kavak"
    text = soup.get_text("\n", strip=True)

    return title, text


async def main(truncate: bool):
    # 1️⃣ Descargar contenido
    title, text = await fetch_kavak_page()
    chunks = chunk_text(text)

    embedder = Embedder()
    vectors = embedder.embed(chunks)

    qdrant = await get_client()
    dim = len(vectors[0])
    await ensure_collection(qdrant, dim)

    async with SessionLocal() as session:
        if truncate:
            await session.execute(delete(KnowledgeChunk))
            await session.commit()

        points: list[PointStruct] = []

        for content, vector in zip(chunks, vectors):
            # Guardar en Postgres
            kc = KnowledgeChunk(
                source=KAVAK_URL,
                title=title,
                content=content,
            )
            session.add(kc)

            # Preparar punto para Qdrant
            pid = stable_point_id(KAVAK_URL, content)
            points.append(
                PointStruct(
                    id=pid,
                    vector=vector,
                    payload={
                        "source": KAVAK_URL,
                        "title": title,
                        "content": content,
                    },
                )
            )

        await session.commit()

    # 2️⃣ Upsert en Qdrant
    await upsert_points(qdrant, points)

    print(
        f"Ingesta completada: {len(chunks)} chunks "
        f"(Postgres + Qdrant collection='{settings.QDRANT_COLLECTION}')"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--truncate", action="store_true")
    args = parser.parse_args()

    asyncio.run(main(truncate=args.truncate))