import os

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "llama3.2:1b")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "8"))
RAG_MIN_SIM = float(os.environ.get("RAG_MIN_SIM", "0.25"))

# nomic-embed-text commonly yields 768 dims; keep configurable so you can swap models later.
EMBED_DIM = int(os.environ.get("EMBED_DIM", "768"))
