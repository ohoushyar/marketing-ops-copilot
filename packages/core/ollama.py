import os
import httpx

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "llama3.1:8b")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

async def embed(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
        )
        r.raise_for_status()
        return r.json()["embedding"]

async def chat(system: str, user: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": CHAT_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
            },
        )
        r.raise_for_status()
        return r.json()["message"]["content"]