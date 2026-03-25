import os
from datetime import date, timedelta
from typing import Optional

import httpx
import typer

app = typer.Typer(no_args_is_help=True)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def _post(path: str, payload: dict, timeout: float = 60.0) -> dict:
    r = httpx.post(f"{API_BASE_URL}{path}", json=payload, timeout=timeout)
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
def ingest(path: str = typer.Argument(..., help="Path to docs directory")):
    data = _post("/ingest", {"path": path}, timeout=600)
    typer.echo(data)


@app.command()
def ask(question: str, citations: bool = typer.Option(False, "--citations")):
    data = _post("/chat", {"question": question, "citations": citations}, timeout=300)
    typer.echo(data["answer"])
    if citations and data.get("citations"):
        typer.echo("\nCitations:")
        for c in data["citations"]:
            typer.echo(f"- {c['source_path']}#{c['chunk_id']}")


@app.command()
def kpi(
    week: str = typer.Option(..., "--week", help="YYYY-MM-DD start of 7-day window"),
    by: str = typer.Option("campaign", "--by", help="Comma-separated group-by columns (e.g. campaign,channel)"),
    data_dir: str = typer.Option("data", "--data-dir", help="Directory containing spend.csv/clicks.csv/conversions.csv"),
):
    by_cols = [b.strip() for b in by.split(",") if b.strip()]
    payload = {"week_start": week, "by": by_cols, "data_dir": data_dir}
    resp = _post("/weekly_kpis", payload, timeout=120)
    _print_table(resp["rows"])


@app.command()
def investigate(
    question: str = typer.Argument(..., help="Investigation prompt (v1 runs a fixed analytics playbook)"),
    week: str = typer.Option(..., "--week", help="YYYY-MM-DD for current week window"),
    by: str = typer.Option("campaign", "--by", help="Comma-separated group-by columns"),
    data_dir: str = typer.Option("data", "--data-dir", help="Directory containing CSV exports"),
    n: int = typer.Option(5, "--n", help="How many movers to show"),
):
    """
    v1 deterministic investigation:
    - compares prior week vs selected week
    - prints delta rows (limited)
    - prints top movers where CAC worsened
    """
    _ = question  # reserved for Day 4 (LLM tool selection). Keep it for UX continuity.

    week_b = date.fromisoformat(week)
    week_a = week_b - timedelta(days=7)

    by_cols = [b.strip() for b in by.split(",") if b.strip()]

    delta_rows = _post(
        "/kpi_delta",
        {
            "week_a_start": week_a.isoformat(),
            "week_b_start": week_b.isoformat(),
            "by": by_cols,
            "data_dir": data_dir,
        },
        timeout=120,
    )["rows"]

    typer.echo(f"\nWeek A: {week_a.isoformat()}  vs  Week B: {week_b.isoformat()}\n")
    typer.echo("Delta (first 20 rows):")
    _print_table(delta_rows, limit=20)

    movers = _post(
        "/top_movers",
        {
            "week_a_start": week_a.isoformat(),
            "week_b_start": week_b.isoformat(),
            "by": by_cols,
            "kpi": "cac",
            "n": n,
            "direction": "worsened",
            "data_dir": data_dir,
        },
        timeout=120,
    )["rows"]

    typer.echo(f"\nTop {n} movers (CAC worsened):")
    _print_table(movers)

    typer.echo("\nNext checks (suggested):")
    typer.echo("- Verify spend mix changes (channel/campaign)")
    typer.echo("- Check CTR and CVR deltas for the worst movers")
    typer.echo("- Check if budget changes happened mid-week (if you log them)")


if __name__ == "__main__":
    app()