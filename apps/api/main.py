import uuid
import json
import time

from fastapi import FastAPI, HTTPException, Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy import text

from packages.core.db import Base, engine, SessionLocal
from packages.core.ingest import ingest_dir
from packages.core.ollama import OllamaError
from packages.core.rag import answer
from packages.core.models import Run
from packages.core.analytics.io import load_data
from packages.core.analytics.kpis import daily_kpis, weekly_aggregate
from packages.core.analytics.compare import kpi_delta as kpi_delta_fn, top_movers as top_movers_fn
from packages.core.analytics.validate import ALLOWED_GROUP_BY
from packages.core.analytics.logging import summarize_rows
from packages.core.models import Run, ToolRun
from packages.core.settings import settings

from apps.api.auth import get_current_user


app = FastAPI(title="Marketing Ops Copilot")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = rid

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        response.headers["X-Request-ID"] = rid
        response.headers["X-Response-Time-ms"] = f"{elapsed_ms:.2f}"
        return response


app.add_middleware(RequestIdMiddleware)


class IngestRequest(BaseModel):
    path: str


class ChatRequest(BaseModel):
    question: str
    citations: bool = True


class WeeklyKpisRequest(BaseModel):
    week_start: str = Field(..., description="YYYY-MM-DD; treated as start of a 7-day window")
    by: list[str] = Field(default_factory=lambda: ["campaign"])
    data_dir: str = "data"


class KpiDeltaRequest(BaseModel):
    week_a_start: str
    week_b_start: str
    by: list[str] = Field(default_factory=lambda: ["campaign"])
    data_dir: str = "data"


class TopMoversRequest(BaseModel):
    week_a_start: str
    week_b_start: str
    by: list[str] = Field(default_factory=lambda: ["campaign"])
    kpi: Literal["cac", "conversions", "roas", "cvr", "ctr", "spend"] = "cac"
    n: int = 10
    direction: Literal["worsened", "improved"] = "worsened"
    data_dir: str = "data"


@app.on_event("startup")
def _startup():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=conn)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ingest")
async def ingest(req: IngestRequest, user_login: str = Depends(get_current_user)):
    with SessionLocal() as session:
        stats = await ingest_dir(session, req.path)
        run_id = str(uuid.uuid4())
        session.add(
            Run(id=run_id, kind="ingest", user_login=user_login, input=req.path, output=str(stats))
        )
        session.commit()
    return {"run_id": run_id, **stats}


@app.post("/chat")
async def chat(req: ChatRequest, user_login: str = Depends(get_current_user)):
    with SessionLocal() as session:
        try:
            res = await answer(session, req.question)
        except OllamaError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        run_id = str(uuid.uuid4())
        session.add(
            Run(
                id=run_id,
                kind="chat",
                user_login=user_login,
                input=req.question,
                output=res["answer"],
            )
        )
        session.commit()
    if not req.citations:
        res["citations"] = []
    res["run_id"] = run_id
    return res


@app.post("/analytics/weekly_kpis")
def weekly_kpis(req: WeeklyKpisRequest):
    bundle = load_data(req.data_dir)
    df_daily = daily_kpis(bundle)
    df_week = weekly_aggregate(df_daily, week_start=req.week_start, by=req.by)
    return {"rows": df_week.to_dict(orient="records")}


@app.post("/analytics/kpi_delta")
def kpi_delta(req: KpiDeltaRequest):
    bundle = load_data(req.data_dir)
    df_daily = daily_kpis(bundle)

    a = weekly_aggregate(df_daily, week_start=req.week_a_start, by=req.by)
    b = weekly_aggregate(df_daily, week_start=req.week_b_start, by=req.by)

    delta = kpi_delta_fn(a, b, by=req.by)
    return {"rows": delta.to_dict(orient="records")}


@app.post("/analytics/top_movers")
def top_movers(req: TopMoversRequest):
    bundle = load_data(req.data_dir)
    df_daily = daily_kpis(bundle)

    a = weekly_aggregate(df_daily, week_start=req.week_a_start, by=req.by)
    b = weekly_aggregate(df_daily, week_start=req.week_b_start, by=req.by)

    delta = kpi_delta_fn(a, b, by=req.by)

    # For CAC: higher is worse. For ROAS/Conversions: lower is worse.
    if req.kpi == "cac":
        ascending = True if req.direction == "improved" else False
    else:
        ascending = False if req.direction == "improved" else True

    movers = top_movers_fn(delta, kpi=req.kpi, n=req.n, ascending=ascending)
    return {"rows": movers.to_dict(orient="records")}


class InvestigateRequest(BaseModel):
    question: str
    week_start: str
    by: list[str] = Field(default_factory=lambda: ["campaign"])
    n: int = 5
    data_dir: str = "data"


@app.post("/analytics/investigate")
async def analytics_investigate(
    req: InvestigateRequest, request: Request, user_login: str = Depends(get_current_user)
):
    bad = [b for b in req.by if b not in ALLOWED_GROUP_BY]
    if bad:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid group-by fields: {bad}. Allowed: {sorted(ALLOWED_GROUP_BY)}",
        )

    from packages.core.analytics.investigate import investigate as investigate_fn

    with SessionLocal() as session:
        run_id = str(uuid.uuid4())

        # run the investigation (LLM plans, pandas executes)
        res = await investigate_fn(req.question, req.week_start, data_dir=req.data_dir)

        # log run
        session.add(
            Run(
                id=run_id,
                kind="analytics_investigate",
                user_login=user_login,
                input=json.dumps(
                    {**req.model_dump(), "request_id": getattr(request.state, "request_id", None)}
                ),
                output=res.get("answer", ""),
            )
        )

        # log summarized tool runs (store only top ~50 rows, clipped cells)
        for tr in res.get("tool_runs", []):
            session.add(
                ToolRun(
                    id=str(uuid.uuid4()),
                    run_id=run_id,
                    tool=str(tr.get("tool")),
                    input_json=json.dumps(tr.get("input", {})),
                    output_json=summarize_rows(
                        tr.get("rows", []), max_rows=settings.analytics_max_rows
                    ),
                    user_login=user_login,
                )
            )

        session.commit()

    return {"run_id": run_id, **res}
