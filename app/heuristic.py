"""System D: keyword-and-length heuristic. Intentionally simple baseline."""

from __future__ import annotations

import re

from gen.kb import ABSTAIN_REASONS, train_entries

DEFER_HINTS = (
    "and",
    "also",
    "plus",
    "if i",
    "during",
    "both",
    "interact",
    "together",
)
ABSTAIN_HINTS = (
    "aadhaar",
    "pan ",
    "password",
    "cvv",
    "card is",
    "sue",
    "fraud",
    "stolen",
    "compensation",
    "recipe",
    "quicksort",
    "cricket",
    "mongolia",
    "breakup",
)
MISSING_HINTS = ("my order", "fit me", "in olive", "where is my")


def route(question: str) -> dict:
    q = question.lower()
    if any(h in q for h in ABSTAIN_HINTS):
        gold = ABSTAIN_REASONS["human_refund_dispute"] if "fraud" in q or "sue" in q else ABSTAIN_REASONS["off_topic"]
        if "aadhaar" in q or "cvv" in q or "password" in q:
            gold = ABSTAIN_REASONS["personal_data"]
        return {"route": "ABSTAIN", "answer": gold, "confidence": 0.55}
    if any(h in q for h in MISSING_HINTS) and not re.search(r"\bft-\d+", q):
        return {"route": "ABSTAIN", "answer": ABSTAIN_REASONS["missing_order"], "confidence": 0.5}
    if len(q.split()) > 28 or sum(q.count(h) for h in DEFER_HINTS) >= 2:
        return {
            "route": "DEFER",
            "answer": "This looks like two policies at once. A larger model should answer.",
            "confidence": 0.4,
        }
    for entry in train_entries():
        if any(k in q for k in entry["keywords"]):
            return {"route": "ANSWER", "answer": entry["answer"], "confidence": 0.6}
    return {"route": "DEFER", "answer": "Heuristic is unsure.", "confidence": 0.3}
