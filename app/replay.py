from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / "results" / "replay_cache.json"


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {"mode": "empty", "items": []}
    return json.loads(CACHE_PATH.read_text(encoding="utf-8"))


def lookup(question: str) -> dict | None:
    cache = load_cache()
    needle = " ".join(question.lower().split())
    for item in cache.get("items", []):
        if " ".join(item["question"].lower().split()) == needle:
            return item
    return None
