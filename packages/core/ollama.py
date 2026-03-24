import httpx

from .config import OLLAMA_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL


class OllamaError(RuntimeError):
    pass


def _detail_from_response(response: httpx.Response) -> str:
    try:
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            return str(data["error"])
    except Exception:
        pass
    return response.text[:300] or f"HTTP {response.status_code}"

async def embed(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            )
            r.raise_for_status()
            # print(f"Embeding result of test input (truncated): {r.json()}...")  # Debug print
            return r.json()["embedding"]
        except httpx.HTTPStatusError as exc:
            detail = _detail_from_response(exc.response)
            raise OllamaError(
                f"Ollama embed request failed ({exc.response.status_code}): {detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise OllamaError(f"Cannot reach Ollama at {OLLAMA_URL}") from exc

async def chat(system: str, user: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            r = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_CHAT_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                },
            )
            r.raise_for_status()
            return r.json()["message"]["content"]
        except httpx.HTTPStatusError as exc:
            detail = _detail_from_response(exc.response)
            raise OllamaError(
                f"Ollama chat request failed ({exc.response.status_code}): {detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise OllamaError(f"Cannot reach Ollama at {OLLAMA_URL}") from exc