import os
import json
from typing import Optional
import uuid

import httpx
import typer

from packages.core.settings import settings

API_BASE_URL = os.environ.get("API_BASE_URL", settings.api_base_url)
REQUEST_ID: str | None = None

app = typer.Typer(no_args_is_help=True)


@app.callback()
def _main():
    """
    Runs before every command; sets a single request id for this CLI invocation.
    """
    global REQUEST_ID
    REQUEST_ID = str(uuid.uuid4())
    typer.echo(f"Request-ID: {REQUEST_ID}", err=True)


def _post(path: str, payload: dict, timeout: float = 60.0) -> dict:
    rid = REQUEST_ID or str(uuid.uuid4())
    headers = {"X-Request-ID": rid}
    r = httpx.post(f"{API_BASE_URL}{path}", json=payload, timeout=timeout, headers=headers)
    r.raise_for_status()
    return r.json()


def _print_table(rows: list[dict], limit: Optional[int] = None) -> None:
    if not rows:
        typer.echo("(no rows)")
        return
    if limit is not None:
        rows = rows[:limit]

    cols = list(rows[0].keys())
    widths = {c: max(len(c), max(len(str(r.get(c, ""))) for r in rows)) for c in cols}

    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    typer.echo(header)
    typer.echo(sep)
    for r in rows:
        typer.echo(" | ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols))


@app.command()
def ingest(
    path: str = typer.Argument(..., help="Path to docs directory"),
    json_output: bool = typer.Option(False, "--json", help="Print raw JSON response"),
):
    data = _post("/ingest", {"path": path}, timeout=600)
    if json_output:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    typer.echo(data)


@app.command()
def ask(
    question: str,
    citations: bool = typer.Option(False, "--citations"),
    json_output: bool = typer.Option(False, "--json", help="Print raw JSON response"),
):
    data = _post("/chat", {"question": question, "citations": citations}, timeout=300)
    if json_output:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    typer.echo(data["answer"])
    if citations and data.get("citations"):
        typer.echo("\nCitations:")
        for c in data["citations"]:
            typer.echo(f"- {c['source_path']}#{c['chunk_id']}")
    if data.get("run_id"):
        typer.echo(f"Run: {data['run_id']}")


@app.command()
def kpi(
    week: str = typer.Option(..., "--week", help="YYYY-MM-DD start of 7-day window"),
    by: str = typer.Option(
        "campaign", "--by", help="Comma-separated group-by columns (e.g. campaign,channel)"
    ),
    data_dir: str = typer.Option(
        "data", "--data-dir", help="Directory containing spend.csv/clicks.csv/conversions.csv"
    ),
    json_output: bool = typer.Option(False, "--json", help="Print raw JSON response"),
):
    by_cols = [b.strip() for b in by.split(",") if b.strip()]
    payload = {"week_start": week, "by": by_cols, "data_dir": data_dir}
    resp = _post("/analytics/weekly_kpis", payload, timeout=120)
    if json_output:
        typer.echo(json.dumps(resp, indent=2, ensure_ascii=False))
        return
    _print_table(resp["rows"])


@app.command()
def investigate(
    question: str = typer.Argument(..., help="Investigation prompt (LLM + tools)"),
    week: str = typer.Option(..., "--week", help="YYYY-MM-DD for current week window"),
    by: str = typer.Option("campaign", "--by", help="Comma-separated group-by columns"),
    data_dir: str = typer.Option("data", "--data-dir", help="Directory containing CSV exports"),
    n: int = typer.Option(5, "--n", help="How many movers to show (hint to planner)"),
    show_tools: bool = typer.Option(
        True, "--show-tools/--no-show-tools", help="Print tool outputs"
    ),
    json_output: bool = typer.Option(False, "--json", help="Print raw JSON response"),
):
    """
    Day 4 investigation:
    - calls /analytics/investigate which uses the LLM to plan tool calls
    - API executes tools deterministically (pandas)
    - API returns answer + tool_runs for grounding
    """
    by_cols = [b.strip() for b in by.split(",") if b.strip()]

    resp = _post(
        "/analytics/investigate",
        {
            "question": question,
            "week_start": week,
            "by": by_cols,
            "n": n,
            "data_dir": data_dir,
        },
        timeout=300,
    )

    if json_output:
        typer.echo(json.dumps(resp, indent=2, ensure_ascii=False))
        return

    typer.echo(resp["answer"])

    if show_tools:
        typer.echo("\nTool runs:")
        for i, tr in enumerate(resp.get("tool_runs", []), start=1):
            typer.echo(f"\n[{i}] tool={tr.get('tool')}")
            typer.echo(f"input={tr.get('input')}")
            _print_table(tr.get("rows", []), limit=20)

    if resp.get("run_id"):
        typer.echo(f"Run: {resp['run_id']}")


@app.command()
def eval():
    import subprocess
    import sys

    raise SystemExit(subprocess.call([sys.executable, "scripts/eval.py"]))


if __name__ == "__main__":
    app()
