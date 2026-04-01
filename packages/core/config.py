from .settings import settings

OLLAMA_URL = settings.ollama_base_url
OLLAMA_CHAT_MODEL = settings.ollama_chat_model
OLLAMA_EMBED_MODEL = settings.ollama_embed_model

API_BASE_URL = settings.api_base_url

RAG_TOP_K = settings.rag_top_k
RAG_MIN_SIM = settings.rag_min_sim

# Keep configurable so embedding models can be swapped later.
EMBED_DIM = settings.embed_dim
