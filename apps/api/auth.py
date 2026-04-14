from __future__ import annotations

from fastapi import Header, HTTPException

from packages.core.settings import settings


def get_current_user(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> str:
    """
    Returns user_login derived from API key.

    Anonymous mode:
      If COPILOT_API_KEYS is empty, allow requests and return "anonymous".

    Auth mode:
      If COPILOT_API_KEYS is set, require X-API-Key to be present and valid.
    """
    if not settings.copilot_api_keys:
        return "anonymous"

    if not x_api_key or x_api_key not in settings.copilot_api_keys:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    return settings.copilot_api_key_map.get(x_api_key, "unknown")
