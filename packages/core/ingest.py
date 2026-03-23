from __future__ import annotations

import hashlib
from pathlib import Path
from sqlalchemy.orm import Session

from .models import Document, Chunk
from .ollama import embed

def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def chunk_markdown(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    # simple, deterministic baseline: paragraph-ish splitting with overlap
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in parts:
        if len(buf) + len(p) + 2 <= max_chars:
            buf = (buf + "\n\n" + p).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)

    if overlap and chunks:
        overlapped = []
        for i, c in enumerate(chunks):
            if i == 0:
                overlapped.append(c)
                continue
            prev = chunks[i - 1]
            tail = prev[-overlap:]
            overlapped.append((tail + "\n\n" + c).strip())
        return overlapped
    return chunks

async def ingest_dir(session: Session, docs_path: str) -> dict:
    root = Path(docs_path)
    md_files = sorted([p for p in root.rglob("*.md") if p.is_file()])

    docs_added = 0
    chunks_added = 0

    for path in md_files:
        content = path.read_text(encoding="utf-8")
        content_hash = _sha1(content)
        doc_id = _sha1(str(path) + ":" + content_hash)

        existing = session.get(Document, doc_id)
        if existing:
            continue

        doc = Document(id=doc_id, source_path=str(path), content_hash=content_hash)
        session.add(doc)

        chunks = chunk_markdown(content)
        for idx, chunk_text in enumerate(chunks):
            emb = await embed(chunk_text)
            chunk_id = _sha1(f"{doc_id}:{idx}")
            session.add(
                Chunk(
                    id=chunk_id,
                    document_id=doc_id,
                    chunk_index=idx,
                    content=chunk_text,
                    embedding=emb,
                )
            )
            chunks_added += 1

        docs_added += 1

    session.commit()
    return {"docs_added": docs_added, "chunks_added": chunks_added, "files_seen": len(md_files)}