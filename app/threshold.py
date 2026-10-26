"""Python owns the safety default. The model never gets the last word on ANSWER."""

from __future__ import annotations

import re
from dataclasses import dataclass

ROUTES = ("ANSWER", "DEFER", "ABSTAIN")

_ROUTE_RE = re.compile(r"ROUTE:\s*(ANSWER|DEFER|ABSTAIN)", re.I)
_ANSWER_RE = re.compile(r"ANSWER:\s*(.*)", re.S)


@dataclass(frozen=True)
class ParsedRouter:
    route: str | None
    answer: str
    raw: str
    malformed: bool


def parse_router_output(text: str) -> ParsedRouter:
    raw = (text or "").strip()
    route_m = _ROUTE_RE.search(raw)
    answer_m = _ANSWER_RE.search(raw)
    route = route_m.group(1).upper() if route_m else None
    answer = answer_m.group(1).strip() if answer_m else raw
    return ParsedRouter(
        route=route,
        answer=answer,
        raw=raw,
        malformed=route is None,
    )


def apply_threshold(
    parsed: ParsedRouter,
    threshold: float,
    logprob_conf: float | None = None,
) -> tuple[str, str]:
    """Return (final_route, reason), using model probabilities for ANSWER confidence."""
    if parsed.malformed or parsed.route is None:
        return "DEFER", "malformed_or_missing_fields"
    if parsed.route not in ROUTES:
        return "DEFER", "unknown_route"
    if parsed.route == "ANSWER":
        if logprob_conf is None:
            return "DEFER", "missing_confidence"
        if logprob_conf < threshold:
            return "DEFER", "below_threshold"
    return parsed.route, "model"


def dangerous_error(predicted: str, gold: str) -> bool:
    return predicted == "ANSWER" and gold in {"DEFER", "ABSTAIN"}
