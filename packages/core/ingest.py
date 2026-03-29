from __future__ import annotations

import hashlib
import re
from pathlib import Path
from sqlalchemy.orm import Session

from .models import Document, Chunk
from .ollama import embed


def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


_heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def split_by_headings(md: str) -> list[tuple[str, str]]:
    """
    Returns list of (section_title, section_text).
    If no headings, returns a single section.
    """
    matches = list(_heading_re.finditer(md))
    if not matches:
        return [("", md.strip())]

    sections: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        title = m.group(0).strip()
        body = md[m.end() : end].strip()
        text = (title + "\n" + body).strip()
        sections.append((title, text))
    return sections


def chunk_text(text: str, max_chars: int = 1400, overlap: int = 150) -> list[str]:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        candidate = (buf + "\n\n" + p).strip() if buf else p
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        # if paragraph itself is huge, hard-split
        if len(p) > max_chars:
            for j in range(0, len(p), max_chars):
                chunks.append(p[j : j + max_chars])
            buf = ""
        else:
            buf = p
    if buf:
        chunks.append(buf)

    if overlap and len(chunks) > 1:
        out = [chunks[0]]
        for i in range(1, len(chunks)):
            out.append((chunks[i - 1][-overlap:] + "\n\n" + chunks[i]).strip())
        return out
    return chunks


def chunk_markdown(md: str, max_chars: int = 1400, overlap: int = 150) -> list[str]:
    sections = split_by_headings(md)
    out: list[str] = []
    for _, sec_text in sections:
        if not sec_text:
            continue
        out.extend(chunk_text(sec_text, max_chars=max_chars, overlap=overlap))
    return out


async def ingest_dir(session: Session, docs_path: str) -> dict:
    root = Path(docs_path)
    md_files = sorted([p for p in root.rglob("*.md") if p.is_file()])

    docs_added = 0
    chunks_added = 0

    for path in md_files:
        content = path.read_text(encoding="utf-8")
        content_hash = _sha1(content)
        doc_id = _sha1(str(path) + ":" + content_hash)

        if session.get(Document, doc_id):
            continue

        doc = Document(id=doc_id, source_path=str(path), content_hash=content_hash)
        session.add(doc)

        chunks = chunk_markdown(content)
        for idx, chunk_text_ in enumerate(chunks):
            chunk_hash = _sha1(chunk_text_)
            emb = await embed(chunk_text_)
            chunk_id = _sha1(f"{doc_id}:{idx}:{chunk_hash}")  # stable + content-sensitive
            session.add(
                Chunk(
                    id=chunk_id,
                    document_id=doc_id,
                    chunk_index=idx,
                    content=chunk_text_,
                    embedding=emb,
                )
            )
            chunks_added += 1

        docs_added += 1

    session.commit()
    return {"docs_added": docs_added, "chunks_added": chunks_added, "files_seen": len(md_files)}
