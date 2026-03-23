import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text

from packages.core.db import Base, engine, SessionLocal
from packages.core.ingest import ingest_dir
from packages.core.rag import answer
from packages.core.models import Run

app = FastAPI(title="Marketing Ops Copilot")

class IngestRequest(BaseModel):
    path: str

class ChatRequest(BaseModel):
    question: str
    citations: bool = True

@app.on_event("startup")
def _startup():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=conn)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest")
async def ingest(req: IngestRequest):
    with SessionLocal() as session:
        stats = await ingest_dir(session, req.path)
        run_id = str(uuid.uuid4())
        session.add(Run(id=run_id, kind="ingest", input=req.path, output=str(stats)))
        session.commit()
    return {"run_id": run_id, **stats}

@app.post("/chat")
async def chat(req: ChatRequest):
    with SessionLocal() as session:
        res = await answer(session, req.question)
        run_id = str(uuid.uuid4())
        session.add(Run(id=run_id, kind="chat", input=req.question, output=res["answer"]))
        session.commit()
    if not req.citations:
        res["citations"] = []
    res["run_id"] = run_id
    return res