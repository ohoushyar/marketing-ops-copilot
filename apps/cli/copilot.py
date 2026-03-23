import os
import typer
import httpx

app = typer.Typer(no_args_is_help=True)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

@app.command()
def ingest(path: str = typer.Argument(..., help="Path to docs directory")):
    r = httpx.post(f"{API_BASE_URL}/ingest", json={"path": path}, timeout=600)
    r.raise_for_status()
    typer.echo(r.json())

@app.command()
def ask(question: str, citations: bool = typer.Option(False, "--citations")):
    r = httpx.post(
        f"{API_BASE_URL}/chat",
        json={"question": question, "citations": citations},
        timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    typer.echo(data["answer"])
    if citations and data.get("citations"):
        typer.echo("\nCitations:")
        for c in data["citations"]:
            typer.echo(f"- {c['source_path']}#{c['chunk_id']}")

if __name__ == "__main__":
    app()