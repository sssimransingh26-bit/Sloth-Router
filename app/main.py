from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.rate_limit import allow
from app.replay import load_cache, lookup
from app.spend import add_and_check, current

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
RESULTS = ROOT / "results"

THRESHOLD = float(os.getenv("ANSWER_THRESHOLD", "0.72"))
DAILY_CAP = float(os.getenv("DAILY_SPEND_CAP_USD", "2.00"))
RATE = int(os.getenv("RATE_LIMIT_PER_HOUR", "20"))
MAX_CHARS = int(os.getenv("MAX_REQUEST_CHARS", "2000"))
TIMEOUT = float(os.getenv("CALL_TIMEOUT_SEC", "20"))
FORCE_REPLAY = os.getenv("FORCE_REPLAY", "0") == "1"

app = FastAPI(title="Sloth Router", version="0.1.0")
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")


class AskBody(BaseModel):
    question: str = Field(min_length=1)


def _has_key() -> bool:
    return bool(os.getenv("TINKER_API_KEY")) and not FORCE_REPLAY


def _status() -> dict:
    results = {}
    table = RESULTS / "table.json"
    if table.exists():
        results = json.loads(table.read_text(encoding="utf-8"))
    cache = load_cache()
    return {
        "live": _has_key(),
        "mode": "live" if _has_key() else "replay",
        "threshold": THRESHOLD,
        "daily_spend_usd": round(current(), 6),
        "daily_cap_usd": DAILY_CAP,
        "router_path": os.getenv("TINKER_ROUTER_PATH") or None,
        "has_benchmark": bool(results),
        "replay_items": len(cache.get("items", [])),
        "results": results,
    }


@app.get("/health")
def health():
    return {"ok": True, **_status()}


@app.get("/api/status")
def status():
    return _status()


@app.get("/api/examples")
def examples():
    return load_cache().get("items", [])


@app.post("/api/ask")
async def ask(body: AskBody, request: Request):
    question = body.question.strip()
    if len(question) > MAX_CHARS:
        return JSONResponse({"error": "Question is too long.", "mode": "error"}, status_code=400)
    ip = request.client.host if request.client else "unknown"
    if not allow(ip, RATE):
        return JSONResponse({"error": "Rate limit: 20 questions per hour per IP.", "mode": "error"}, status_code=429)

    if not _has_key():
        hit = lookup(question)
        if hit:
            return {**hit, "mode": "replay", "badge": "replay"}
        return {
            "mode": "replay",
            "badge": "replay",
            "route": None,
            "answer": "Replay mode has no cached route for this wording. Try a demo question on the landing page, or set TINKER_API_KEY for live routing.",
            "cost_usd": 0.0,
            "latency_ms": 0,
            "reason": "uncached_replay",
        }

    try:
        from app.tinker_backend import live_route

        result = await live_route(question, THRESHOLD, TIMEOUT)
    except TimeoutError:
        hit = lookup(question)
        if hit:
            return {**hit, "mode": "replay", "badge": "timeout-fallback", "reason": "timeout"}
        return {
            "mode": "live",
            "route": "DEFER",
            "answer": "The router timed out after 20 seconds, so this request was deferred rather than answered cheaply.",
            "reason": "timeout",
            "cost_usd": 0.0,
            "latency_ms": int(TIMEOUT * 1000),
        }
    except Exception as exc:  # noqa: BLE001 — surface the failure, do not invent an ANSWER
        return JSONResponse(
            {
                "error": "Live routing failed; not answering blindly.",
                "detail": str(exc.__class__.__name__),
                "mode": "error",
            },
            status_code=503,
        )

    ok, spent = add_and_check(result["cost_usd"], DAILY_CAP)
    if not ok:
        hit = lookup(question)
        payload = hit or {
            "route": None,
            "answer": "Daily spend cap reached. Switching to replay.",
        }
        return {**payload, "mode": "replay", "badge": "spend-cap", "daily_spend_usd": spent}
    result["daily_spend_usd"] = spent
    result["badge"] = "live"
    return result


@app.get("/")
def index():
    return FileResponse(WEB / "static" / "index.html")
