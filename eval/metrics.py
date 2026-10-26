from __future__ import annotations

import math
from collections import Counter

from app.threshold import dangerous_error

LABELS = ("ANSWER", "DEFER", "ABSTAIN")


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def answer_correct(pred_answer: str, gold_answer: str, gold_route: str, pred_route: str) -> bool:
    if gold_route == "ABSTAIN":
        return pred_route == "ABSTAIN"
    if pred_route == "ABSTAIN":
        return gold_route == "ABSTAIN"
    return _norm(gold_answer) in _norm(pred_answer) or _norm(pred_answer) in _norm(gold_answer)


def confusion(rows: list[dict]) -> dict[str, dict[str, int]]:
    table = {g: {p: 0 for p in LABELS} for g in LABELS}
    for row in rows:
        g = row["gold"]
        p = row["pred"]
        if g in table and p in table[g]:
            table[g][p] += 1
    return table


def prf(table: dict[str, dict[str, int]], label: str) -> dict[str, float]:
    tp = table[label][label]
    fp = sum(table[g][label] for g in LABELS if g != label)
    fn = sum(table[label][p] for p in LABELS if p != label)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"precision": prec, "recall": rec, "f1": f1}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return ((centre - adj) / den, (centre + adj) / den)


def summarize(rows: list[dict], cost_per: list[float], latencies: list[float]) -> dict:
    n = len(rows)
    correct_route = sum(r["pred"] == r["gold"] for r in rows)
    dang = sum(dangerous_error(r["pred"], r["gold"]) for r in rows)
    ans_ok = sum(r["answer_ok"] for r in rows)
    table = confusion(rows)
    per_class = {lab: prf(table, lab) for lab in LABELS}
    lo, hi = wilson(dang, n)
    abstain_rate = sum(r["pred"] == "ABSTAIN" for r in rows) / n if n else 0
    return {
        "n": n,
        "route_acc": correct_route / n if n else 0,
        "dangerous_error": dang / n if n else 0,
        "dangerous_error_ci95": [lo, hi],
        "answer_correct": ans_ok / n if n else 0,
        "abstention_rate": abstain_rate,
        "cost_per_1k_usd": (sum(cost_per) / n * 1000) if n else 0,
        "latency_ms_mean": (sum(latencies) / n) if n else 0,
        "per_class": per_class,
        "label_counts": dict(Counter(r["pred"] for r in rows)),
    }
