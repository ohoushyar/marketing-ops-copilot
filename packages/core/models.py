from __future__ import annotations

import datetime as dt
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .db import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. sha1 of path+content
    source_path: Mapped[str] = mapped_column(String, unique=True, index=True)
    content_hash: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # sha1(doc_id + chunk_index)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    # nomic-embed-text is 768 dims in many setups; make configurable later if needed
    embedding: Mapped[list[float]] = mapped_column(Vector(768))

    document: Mapped["Document"] = relationship(back_populates="chunks")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # uuid
    kind: Mapped[str] = mapped_column(String, index=True)      # "chat" | "ingest"
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    input: Mapped[str] = mapped_column(Text)
    output: Mapped[str] = mapped_column(Text)