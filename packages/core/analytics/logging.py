from __future__ import annotations
import json
from typing import Any


def summarize_rows(rows: list[dict], max_rows: int = 50, max_cell_chars: int = 200) -> str:
    def clip(v: Any) -> Any:
        s = str(v)
        if len(s) > max_cell_chars:
            return s[: max_cell_chars - 3] + "..."
        return v

    out = []
    for r in rows[:max_rows]:
        out.append({k: clip(v) for k, v in r.items()})
    return json.dumps({"rows": out, "truncated": len(rows) > max_rows})
